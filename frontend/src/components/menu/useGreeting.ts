"use client";

import { useEffect, useState } from "react";

function greetingForHour(hour: number): string {
  if (hour < 12) return "Buenos días";
  if (hour < 19) return "Buenas tardes";
  return "Buenas noches";
}

export function useGreeting(): string {
  const [greeting, setGreeting] = useState("Bienvenido");

  useEffect(() => {
    setGreeting(greetingForHour(new Date().getHours()));
  }, []);

  return greeting;
}
