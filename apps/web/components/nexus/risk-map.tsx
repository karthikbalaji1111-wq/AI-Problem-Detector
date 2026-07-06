"use client";

import { useEffect, useRef } from "react";
import { Map, Radar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const riskNodes = [
  { label: "Supply corridor", left: "63%", top: "43%", tone: "amber", score: 0.71 },
  { label: "Factory line", left: "47%", top: "56%", tone: "coral", score: 0.82 },
  { label: "Customer region", left: "31%", top: "38%", tone: "cyan", score: 0.48 },
  { label: "Logistics hub", left: "72%", top: "62%", tone: "green", score: 0.24 }
] as const;

export function RiskMap() {
  const mapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!token || !mapRef.current) return;
    let cleanup = () => {};
    void import("mapbox-gl").then((mapboxgl) => {
      mapboxgl.default.accessToken = token;
      const map = new mapboxgl.default.Map({
        container: mapRef.current as HTMLDivElement,
        style: "mapbox://styles/mapbox/dark-v11",
        center: [-73.985, 40.758],
        zoom: 2.2,
        attributionControl: false
      });
      cleanup = () => map.remove();
    });
    return () => cleanup();
  }, []);

  return (
    <Card className="scanline min-h-[360px]">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Map className="h-4 w-4 text-cyan" />
            Operating Map
          </CardTitle>
          <p className="mt-1 text-xs text-muted">Live risk surface across workforce signals</p>
        </div>
        <Badge tone="cyan">scanning</Badge>
      </CardHeader>
      <CardContent>
        <div className="relative h-[280px] overflow-hidden rounded-lg border border-white/10 bg-[#071016]">
          <div ref={mapRef} className="absolute inset-0 opacity-90" />
          <div className="nexus-grid absolute inset-0" />
          <div className="absolute inset-x-8 top-1/2 h-px bg-cyan/30" />
          <div className="absolute inset-y-8 left-1/2 w-px bg-cyan/20" />
          <div className="absolute left-6 top-6 flex items-center gap-2 text-xs text-muted">
            <Radar className="h-4 w-4 text-cyan" />
            Mapbox layer activates when NEXT_PUBLIC_MAPBOX_TOKEN is configured
          </div>
          {riskNodes.map((node) => (
            <div
              key={node.label}
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{ left: node.left, top: node.top }}
            >
              <div className="relative">
                <div
                  className={`absolute -inset-5 rounded-full blur-xl ${
                    node.tone === "coral"
                      ? "bg-coral/30"
                      : node.tone === "amber"
                        ? "bg-amber/25"
                        : node.tone === "green"
                          ? "bg-success/20"
                          : "bg-cyan/20"
                  }`}
                />
                <div className="relative rounded-md border border-white/15 bg-black/50 px-2 py-1 text-xs">
                  <div className="font-medium text-foreground">{node.label}</div>
                  <div className="text-muted">{Math.round(node.score * 100)} risk</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
