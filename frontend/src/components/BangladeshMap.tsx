import { useState } from "react";
import { BD_MAP_H, BD_MAP_W, DIVISIONS } from "../bdMap";
import { useI18n } from "../i18n";

// Greens only, so the map reads as one country; the red sun behind it echoes the national flag.
const FILLS = [
  "#0a8560",
  "#0c9a6e",
  "#087553",
  "#0eac7a",
  "#097a58",
  "#0b9068",
  "#0a6f50",
  "#0d9f72",
];

export default function BangladeshMap() {
  const { pick } = useI18n();
  const [hover, setHover] = useState<string | null>(null);
  const dhaka = DIVISIONS.find((d) => d.id === "Dhaka");
  const active = DIVISIONS.find((d) => d.id === hover);

  return (
    <figure className="bdmap">
      <svg
        viewBox={`0 0 ${BD_MAP_W} ${BD_MAP_H}`}
        role="img"
        aria-label={pick(
          "Map of Bangladesh with its eight divisions",
          "আটটি বিভাগসহ বাংলাদেশের মানচিত্র",
        )}
      >
        <defs>
          <radialGradient id="sun" cx="45%" cy="40%" r="65%">
            <stop offset="0" stopColor="#ff5a6c" />
            <stop offset="1" stopColor="#d81d33" />
          </radialGradient>
          <filter id="mapShadow" x="-10%" y="-10%" width="120%" height="125%">
            <feDropShadow
              dx="0"
              dy="10"
              stdDeviation="9"
              floodColor="#001a12"
              floodOpacity="0.45"
            />
          </filter>
        </defs>
        <circle
          className="bdmap-sun"
          cx={BD_MAP_W * 0.46}
          cy={BD_MAP_H * 0.47}
          r={BD_MAP_W * 0.43}
          fill="url(#sun)"
        />
        <g filter="url(#mapShadow)">
          {DIVISIONS.map((d, i) => (
            <path
              key={d.id}
              d={d.d}
              fill={FILLS[i % FILLS.length]}
              className={`bdmap-div${hover === d.id ? " is-hover" : ""}`}
              onMouseEnter={() => setHover(d.id)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(d.id)}
              onBlur={() => setHover(null)}
              tabIndex={0}
              aria-label={pick(d.en, d.bn)}
            />
          ))}
        </g>
        <g className="bdmap-labels" aria-hidden="true">
          {DIVISIONS.map((d) => (
            <text key={d.id} x={d.cx} y={d.cy} textAnchor="middle">
              {pick(d.en, d.bn)}
            </text>
          ))}
        </g>
        {dhaka && (
          <g
            className="bdmap-capital"
            transform={`translate(${dhaka.cx + 8} ${dhaka.cy + 22})`}
            aria-hidden="true"
          >
            <circle className="ping" r="6" />
            <circle r="5" />
          </g>
        )}
      </svg>
      <figcaption>
        {active
          ? pick(`${active.en} division`, `${active.bn} বিভাগ`)
          : pick(
              "Eight divisions, one dataset. Hover to explore.",
              "আট বিভাগ, একটি ডেটাসেট। ঘুরে দেখুন।",
            )}
      </figcaption>
    </figure>
  );
}
