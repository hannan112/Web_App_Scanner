"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";

interface City {
  name: string;
  lat: number; // latitude
  lng: number; // longitude
}

interface Particle {
  from: City;
  to: City;
  t: number; // 0..1 along the path
  speed: number; // increment per frame
}

const CITIES: City[] = [
  { name: "San Francisco", lat: 37.7749, lng: -122.4194 },
  { name: "New York", lat: 40.7128, lng: -74.0060 },
  { name: "Sao Paulo", lat: -23.5505, lng: -46.6333 },
  { name: "London", lat: 51.5074, lng: -0.1278 },
  { name: "Berlin", lat: 52.5200, lng: 13.4050 },
  { name: "Dubai", lat: 25.2048, lng: 55.2708 },
  { name: "Mumbai", lat: 19.0760, lng: 72.8777 },
  { name: "Singapore", lat: 1.3521, lng: 103.8198 },
  { name: "Tokyo", lat: 35.6762, lng: 139.6503 },
  { name: "Sydney", lat: -33.8688, lng: 151.2093 },
];

function randomPair(): [City, City] {
  const a = Math.floor(Math.random() * CITIES.length);
  let b = Math.floor(Math.random() * CITIES.length);
  if (b === a) b = (b + 1) % CITIES.length;
  return [CITIES[a], CITIES[b]];
}

export default function WorldMapAnimation() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const particlesRef = useRef<Particle[]>([]);

  useEffect(() => {
    function resize() {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (!canvas || !container) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const { clientWidth, clientHeight } = container;
      canvas.width = Math.floor(clientWidth * dpr);
      canvas.height = Math.floor(clientHeight * dpr);
      canvas.style.width = `${clientWidth}px`;
      canvas.style.height = `${clientHeight}px`;
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  useEffect(() => {
    particlesRef.current = Array.from({ length: 18 }).map(() => {
      const [from, to] = randomPair();
      return { from, to, t: Math.random(), speed: 0.003 + Math.random() * 0.005 };
    });
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    function toPx(city: City) {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;

      // SVG map dimensions from the file: 2100x1312.5
      const mapAspectRatio = 2100 / 1312.5; // ~1.6
      const containerAspectRatio = w / h;

      let mapWidth, mapHeight, offsetX, offsetY;

      // Calculate actual rendered map dimensions (objectFit: contain behavior)
      if (containerAspectRatio > mapAspectRatio) {
        // Container is wider - map is constrained by height
        mapHeight = h;
        mapWidth = h * mapAspectRatio;
        offsetX = (w - mapWidth) / 2;
        offsetY = 0;
      } else {
        // Container is taller - map is constrained by width
        mapWidth = w;
        mapHeight = w / mapAspectRatio;
        offsetX = 0;
        offsetY = (h - mapHeight) / 2;
      }

      // Equirectangular projection within the actual map area
      const x = offsetX + ((city.lng + 180) / 360) * mapWidth;
      const y = offsetY + ((90 - city.lat) / 180) * mapHeight;
      return { x, y };
    }

    function draw() {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);

      ctx.lineWidth = 0.8;
      ctx.strokeStyle = "rgba(37, 99, 235, 0.12)";
      ctx.fillStyle = "rgba(37, 99, 235, 0.9)";

      for (let i = 0; i < CITIES.length; i++) {
        for (let j = i + 1; j < CITIES.length; j++) {
          if ((i + j) % 5 !== 0) continue;
          const a = toPx(CITIES[i]);
          const b = toPx(CITIES[j]);
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          const mx = (a.x + b.x) / 2;
          const my = (a.y + b.y) / 2 - 40;
          ctx.quadraticCurveTo(mx, my, b.x, b.y);
          ctx.stroke();
        }
      }

      particlesRef.current.forEach(p => {
        p.t += p.speed;
        if (p.t >= 1) {
          if (Math.random() < 0.5) {
            const prevTo = p.to;
            p.to = p.from;
            p.from = prevTo;
          } else {
            const [nf, nt] = randomPair();
            p.from = nf;
            p.to = nt;
          }
          p.t = 0;
          p.speed = 0.003 + Math.random() * 0.005;
        }

        const a = toPx(p.from);
        const b = toPx(p.to);
        const cx = (a.x + b.x) / 2;
        const cy = (a.y + b.y) / 2 - 40;
        const x1 = a.x + (cx - a.x) * p.t;
        const y1 = a.y + (cy - a.y) * p.t;
        const x2 = cx + (b.x - cx) * p.t;
        const y2 = cy + (b.y - cy) * p.t;
        const x = x1 + (x2 - x1) * p.t;
        const y = y1 + (y2 - y1) * p.t;

        ctx.beginPath();
        ctx.arc(x, y, 2.2, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(59, 130, 246, 0.95)";
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x - (x2 - x1) * 0.1, y - (y2 - y1) * 0.1);
        ctx.strokeStyle = "rgba(59, 130, 246, 0.25)";
        ctx.lineWidth = 1.2;
        ctx.stroke();
      });

      rafRef.current = requestAnimationFrame(draw);
    }

    rafRef.current = requestAnimationFrame(draw);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <div ref={containerRef} className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
      {/* Dotted World Map Background */}
      <div className="absolute inset-0 opacity-60 flex items-center justify-center">
        <Image
          src="/world-map-dotted.svg"
          alt="World Map"
          fill
          priority
          style={{ objectFit: "contain", objectPosition: "center" }}
        />
      </div>
      {/* Animated Lines Canvas */}
      <canvas ref={canvasRef} className="absolute inset-0" />
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/20 via-transparent to-blue-50/50" />
    </div>
  );
}
