import base64
import os
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

@dataclass(frozen=True)
class ConnectorResult:
    connector: str
    action: str
    ok: bool
    status: str
    data: dict[str, Any]


class Connector:
    key = "base"
    actions: tuple[str, ...] = ()

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def credential(self, name: str, env_name: str | None = None) -> str | None:
        value = self.config.get(name)
        if value:
            return str(value)
        return os.getenv(env_name or f"NEXUS_{self.key.upper()}_{name.upper()}")

    def not_configured(self, action: str, missing: str) -> ConnectorResult:
        return ConnectorResult(self.key, action, False, "not_configured", {"missing": missing})

    async def execute(self, action: str, payload: dict[str, Any]) -> ConnectorResult:
        if action not in self.actions:
            return ConnectorResult(self.key, action, False, "unsupported_action", {"actions": list(self.actions)})
        method = getattr(self, f"action_{action}")
        return await method(payload)


async def parse_response(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        body = {"text": response.text}
    return {"status_code": response.status_code, "body": body}


class SlackConnector(Connector):
    key = "slack"
    actions = ("send_message",)

    async def action_send_message(self, payload: dict[str, Any]) -> ConnectorResult:
        webhook = self.credential("webhook_url", "NEXUS_SLACK_WEBHOOK_URL")
        if not webhook:
            return self.not_configured("send_message", "webhook_url")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook, json={"text": payload["text"]})
        return ConnectorResult(self.key, "send_message", response.is_success, "completed", await parse_response(response))


class DiscordConnector(Connector):
    key = "discord"
    actions = ("send_message",)

    async def action_send_message(self, payload: dict[str, Any]) -> ConnectorResult:
        webhook = self.credential("webhook_url", "NEXUS_DISCORD_WEBHOOK_URL")
        if not webhook:
            return self.not_configured("send_message", "webhook_url")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook, json={"content": payload["text"]})
        return ConnectorResult(self.key, "send_message", response.is_success, "completed", await parse_response(response))


class TeamsConnector(Connector):
    key = "teams"
    actions = ("send_message",)

    async def action_send_message(self, payload: dict[str, Any]) -> ConnectorResult:
        webhook = self.credential("webhook_url", "NEXUS_TEAMS_WEBHOOK_URL")
        if not webhook:
            return self.not_configured("send_message", "webhook_url")
        body = {"type": "message", "text": payload["text"]}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook, json=body)
        return ConnectorResult(self.key, "send_message", response.is_success, "completed", await parse_response(response))


class GmailConnector(Connector):
    key = "gmail"
    actions = ("send_email",)

    async def action_send_email(self, payload: dict[str, Any]) -> ConnectorResult:
        token = self.credential("access_token", "NEXUS_GMAIL_ACCESS_TOKEN")
        if not token:
            return self.not_configured("send_email", "access_token")
        raw = (
            f"To: {payload['to']}\r\n"
            f"Subject: {payload['subject']}\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{payload['body']}"
        )
        encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {token}"},
                json={"raw": encoded},
            )
        return ConnectorResult(self.key, "send_email", response.is_success, "completed", await parse_response(response))


class GoogleCalendarConnector(Connector):
    key = "google_calendar"
    actions = ("create_event",)

    async def action_create_event(self, payload: dict[str, Any]) -> ConnectorResult:
        token = self.credential("access_token", "NEXUS_GOOGLE_CALENDAR_ACCESS_TOKEN")
        calendar_id = self.credential("calendar_id", "NEXUS_GOOGLE_CALENDAR_ID") or "primary"
        if not token:
            return self.not_configured("create_event", "access_token")
        event = {
            "summary": payload["summary"],
            "description": payload.get("description", ""),
            "start": {"dateTime": payload["start"]},
            "end": {"dateTime": payload["end"]},
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                headers={"Authorization": f"Bearer {token}"},
                json=event,
            )
        return ConnectorResult(self.key, "create_event", response.is_success, "completed", await parse_response(response))


class GitHubConnector(Connector):
    key = "github"
    actions = ("create_issue", "list_repo_issues")

    def headers(self) -> dict[str, str] | None:
        token = self.credential("token", "NEXUS_GITHUB_TOKEN")
        if not token:
            return None
        return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    async def action_create_issue(self, payload: dict[str, Any]) -> ConnectorResult:
        headers = self.headers()
        if not headers:
            return self.not_configured("create_issue", "token")
        owner = payload["owner"]
        repo = payload["repo"]
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues",
                headers=headers,
                json={"title": payload["title"], "body": payload.get("body", "")},
            )
        return ConnectorResult(self.key, "create_issue", response.is_success, "completed", await parse_response(response))

    async def action_list_repo_issues(self, payload: dict[str, Any]) -> ConnectorResult:
        headers = self.headers()
        if not headers:
            return self.not_configured("list_repo_issues", "token")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"https://api.github.com/repos/{payload['owner']}/{payload['repo']}/issues",
                headers=headers,
                params={"state": payload.get("state", "open")},
            )
        return ConnectorResult(self.key, "list_repo_issues", response.is_success, "completed", await parse_response(response))


class JiraConnector(Connector):
    key = "jira"
    actions = ("create_issue",)

    async def action_create_issue(self, payload: dict[str, Any]) -> ConnectorResult:
        base_url = self.credential("base_url", "NEXUS_JIRA_BASE_URL")
        email = self.credential("email", "NEXUS_JIRA_EMAIL")
        token = self.credential("api_token", "NEXUS_JIRA_API_TOKEN")
        if not all([base_url, email, token]):
            return self.not_configured("create_issue", "base_url,email,api_token")
        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        body = {
            "fields": {
                "project": {"key": payload["project_key"]},
                "summary": payload["summary"],
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": payload.get("description", "")}],
                        }
                    ],
                },
                "issuetype": {"name": payload.get("issue_type", "Task")},
            }
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/rest/api/3/issue",
                headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
                json=body,
            )
        return ConnectorResult(self.key, "create_issue", response.is_success, "completed", await parse_response(response))


class LinearConnector(Connector):
    key = "linear"
    actions = ("create_issue",)

    async def action_create_issue(self, payload: dict[str, Any]) -> ConnectorResult:
        token = self.credential("api_key", "NEXUS_LINEAR_API_KEY")
        if not token:
            return self.not_configured("create_issue", "api_key")
        query = """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) { success issue { id identifier url title } }
        }
        """
        variables = {
            "input": {
                "teamId": payload["team_id"],
                "title": payload["title"],
                "description": payload.get("description", ""),
            }
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.linear.app/graphql",
                headers={"Authorization": token},
                json={"query": query, "variables": variables},
            )
        return ConnectorResult(self.key, "create_issue", response.is_success, "completed", await parse_response(response))


class NotionConnector(Connector):
    key = "notion"
    actions = ("create_page",)

    async def action_create_page(self, payload: dict[str, Any]) -> ConnectorResult:
        token = self.credential("token", "NEXUS_NOTION_TOKEN")
        database_id = payload.get("database_id") or self.credential("database_id", "NEXUS_NOTION_DATABASE_ID")
        if not all([token, database_id]):
            return self.not_configured("create_page", "token,database_id")
        body = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": payload["title"]}}]},
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": payload.get("body", "")}}]},
                }
            ],
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.notion.com/v1/pages",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                json=body,
            )
        return ConnectorResult(self.key, "create_page", response.is_success, "completed", await parse_response(response))


class DriveConnector(Connector):
    key = "drive"
    actions = ("list_files",)

    async def action_list_files(self, payload: dict[str, Any]) -> ConnectorResult:
        token = self.credential("access_token", "NEXUS_DRIVE_ACCESS_TOKEN")
        if not token:
            return self.not_configured("list_files", "access_token")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": payload.get("query"), "pageSize": payload.get("page_size", 20)},
            )
        return ConnectorResult(self.key, "list_files", response.is_success, "completed", await parse_response(response))


class DropboxConnector(Connector):
    key = "dropbox"
    actions = ("list_folder",)

    async def action_list_folder(self, payload: dict[str, Any]) -> ConnectorResult:
        token = self.credential("access_token", "NEXUS_DROPBOX_ACCESS_TOKEN")
        if not token:
            return self.not_configured("list_folder", "access_token")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.dropboxapi.com/2/files/list_folder",
                headers={"Authorization": f"Bearer {token}"},
                json={"path": payload.get("path", "")},
            )
        return ConnectorResult(self.key, "list_folder", response.is_success, "completed", await parse_response(response))


class WeatherConnector(Connector):
    key = "weather"
    actions = ("forecast",)

    async def action_forecast(self, payload: dict[str, Any]) -> ConnectorResult:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": payload["latitude"],
                    "longitude": payload["longitude"],
                    "hourly": "temperature_2m,precipitation,wind_speed_10m",
                    "forecast_days": payload.get("forecast_days", 3),
                },
            )
        return ConnectorResult(self.key, "forecast", response.is_success, "completed", await parse_response(response))


class NewsConnector(Connector):
    key = "news"
    actions = ("search",)

    async def action_search(self, payload: dict[str, Any]) -> ConnectorResult:
        token = self.credential("api_key", "NEXUS_NEWS_API_KEY")
        if not token:
            return self.not_configured("search", "api_key")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params={"q": payload["query"], "pageSize": payload.get("page_size", 10), "apiKey": token},
            )
        return ConnectorResult(self.key, "search", response.is_success, "completed", await parse_response(response))


class TwilioConnector(Connector):
    key = "twilio"
    actions = ("send_sms",)

    async def action_send_sms(self, payload: dict[str, Any]) -> ConnectorResult:
        account_sid = self.credential("account_sid", "NEXUS_TWILIO_ACCOUNT_SID")
        auth_token = self.credential("auth_token", "NEXUS_TWILIO_AUTH_TOKEN")
        from_number = self.credential("from_number", "NEXUS_TWILIO_FROM_NUMBER")
        if not all([account_sid, auth_token, from_number]):
            return self.not_configured("send_sms", "account_sid,auth_token,from_number")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                auth=(account_sid, auth_token),
                data={"From": from_number, "To": payload["to"], "Body": payload["body"]},
            )
        return ConnectorResult(self.key, "send_sms", response.is_success, "completed", await parse_response(response))


class MapsConnector(Connector):
    key = "maps"
    actions = ("geocode",)

    async def action_geocode(self, payload: dict[str, Any]) -> ConnectorResult:
        token = self.credential("api_key", "NEXUS_GOOGLE_MAPS_API_KEY")
        if not token:
            return self.not_configured("geocode", "api_key")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": payload["address"], "key": token},
            )
        return ConnectorResult(self.key, "geocode", response.is_success, "completed", await parse_response(response))


class SupabaseConnector(Connector):
    key = "supabase"
    actions = ("select", "insert")

    def headers(self) -> dict[str, str] | None:
        key = self.credential("service_role_key", "NEXUS_SUPABASE_SERVICE_ROLE_KEY")
        if not key:
            return None
        return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    async def action_select(self, payload: dict[str, Any]) -> ConnectorResult:
        url = self.credential("url", "NEXUS_SUPABASE_URL")
        headers = self.headers()
        if not url or not headers:
            return self.not_configured("select", "url,service_role_key")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{url.rstrip('/')}/rest/v1/{payload['table']}",
                headers=headers,
                params=payload.get("params", {}),
            )
        return ConnectorResult(self.key, "select", response.is_success, "completed", await parse_response(response))

    async def action_insert(self, payload: dict[str, Any]) -> ConnectorResult:
        url = self.credential("url", "NEXUS_SUPABASE_URL")
        headers = self.headers()
        if not url or not headers:
            return self.not_configured("insert", "url,service_role_key")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{url.rstrip('/')}/rest/v1/{payload['table']}",
                headers={**headers, "Prefer": "return=representation"},
                json=payload["rows"],
            )
        return ConnectorResult(self.key, "insert", response.is_success, "completed", await parse_response(response))


class PineconeConnector(Connector):
    key = "pinecone"
    actions = ("query", "upsert")

    def headers(self) -> dict[str, str] | None:
        token = self.credential("api_key", "NEXUS_PINECONE_API_KEY")
        if not token:
            return None
        return {"Api-Key": token, "Content-Type": "application/json"}

    async def action_query(self, payload: dict[str, Any]) -> ConnectorResult:
        host = self.credential("host", "NEXUS_PINECONE_HOST")
        headers = self.headers()
        if not host or not headers:
            return self.not_configured("query", "host,api_key")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"https://{host}/query", headers=headers, json=payload)
        return ConnectorResult(self.key, "query", response.is_success, "completed", await parse_response(response))

    async def action_upsert(self, payload: dict[str, Any]) -> ConnectorResult:
        host = self.credential("host", "NEXUS_PINECONE_HOST")
        headers = self.headers()
        if not host or not headers:
            return self.not_configured("upsert", "host,api_key")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"https://{host}/vectors/upsert", headers=headers, json=payload)
        return ConnectorResult(self.key, "upsert", response.is_success, "completed", await parse_response(response))


class QdrantConnector(Connector):
    key = "qdrant"
    actions = ("search", "upsert")

    def headers(self) -> dict[str, str]:
        token = self.credential("api_key", "NEXUS_QDRANT_API_KEY")
        return {"api-key": token} if token else {}

    async def action_search(self, payload: dict[str, Any]) -> ConnectorResult:
        url = self.credential("url", "NEXUS_QDRANT_URL")
        if not url:
            return self.not_configured("search", "url")
        collection = payload["collection"]
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{url.rstrip('/')}/collections/{collection}/points/search",
                headers=self.headers(),
                json={"vector": payload["vector"], "limit": payload.get("limit", 10)},
            )
        return ConnectorResult(self.key, "search", response.is_success, "completed", await parse_response(response))

    async def action_upsert(self, payload: dict[str, Any]) -> ConnectorResult:
        url = self.credential("url", "NEXUS_QDRANT_URL")
        if not url:
            return self.not_configured("upsert", "url")
        collection = payload["collection"]
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.put(
                f"{url.rstrip('/')}/collections/{collection}/points",
                headers=self.headers(),
                json={"points": payload["points"]},
            )
        return ConnectorResult(self.key, "upsert", response.is_success, "completed", await parse_response(response))


class PostgresConnector(Connector):
    key = "postgres"
    actions = ("query",)

    async def action_query(self, payload: dict[str, Any]) -> ConnectorResult:
        if not payload["sql"].lstrip().lower().startswith("select"):
            return ConnectorResult(self.key, "query", False, "rejected", {"reason": "Only SELECT queries are allowed"})
        from nexus_api.database import engine

        with Session(engine) as db:
            rows = db.execute(text(payload["sql"]), payload.get("params", {})).mappings().all()
            data = {"rows": [dict(row) for row in rows[: payload.get("limit", 100)]]}
        return ConnectorResult(self.key, "query", True, "completed", data)


CONNECTOR_CLASSES: tuple[type[Connector], ...] = (
    SlackConnector,
    DiscordConnector,
    TeamsConnector,
    GmailConnector,
    GoogleCalendarConnector,
    GitHubConnector,
    JiraConnector,
    LinearConnector,
    NotionConnector,
    DriveConnector,
    DropboxConnector,
    WeatherConnector,
    NewsConnector,
    TwilioConnector,
    MapsConnector,
    SupabaseConnector,
    PineconeConnector,
    QdrantConnector,
    PostgresConnector,
)

CONNECTORS = {connector.key: connector for connector in CONNECTOR_CLASSES}


def connector_actions() -> dict[str, list[str]]:
    return {key: list(connector.actions) for key, connector in CONNECTORS.items()}


def build_connector(key: str, config: dict[str, Any] | None = None) -> Connector:
    connector_class = CONNECTORS[key]
    return connector_class(config)
