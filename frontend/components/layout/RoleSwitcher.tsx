"use client";

import { useEffect, useRef, useState } from "react";
import { useRole } from "@/providers/RoleProvider";

type Role = "students" | "professional";

const ROLES: { value: Role; label: string }[] = [
  {
    value: "students",
    label: "Students",
  },
  {
    value: "professional",
    label: "Professional",
  },
];

export default function RoleSwitcher() {
  const { role, setRole } = useRole();

  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const currentRole =
    ROLES.find((item) => item.value === role)?.label ?? "Students";

  return (
    <div ref={dropdownRef} className="relative w-44">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-9 w-full items-center justify-between rounded-lg border border-white/10 bg-[#1a1a1a] px-4 text-sm font-medium text-white transition-all duration-200 hover:border-[#ff8a2a] hover:bg-[#222]"
      >
        <span>{currentRole}</span>

        <svg
          className={`h-4 w-4 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 9l6 6 6-6"
          />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-full overflow-hidden rounded-lg border border-white/10 bg-[#161616] shadow-2xl">
          {ROLES.map((item) => (
            <button
              key={item.value}
              type="button"
              onClick={() => {
                setRole(item.value);
                setOpen(false);
              }}
              className={`block w-full px-4 py-2.5 text-left text-sm transition-colors ${
                role === item.value
                  ? "bg-[#ff8a2a] text-black"
                  : "text-white hover:bg-white/10"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}