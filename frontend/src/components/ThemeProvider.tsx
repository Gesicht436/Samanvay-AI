"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { getInitialTheme, applyTheme } from "@/lib/theme";

interface ThemeContextType {
  theme: "light" | "dark";
  toggleTheme: () => void;
  activeCpse: string;
  setActiveCpse: (cpse: string) => void;
  activeDepot: string;
  setActiveDepot: (depot: string) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "light",
  toggleTheme: () => {},
  activeCpse: "IOCL",
  setActiveCpse: () => {},
  activeDepot: "DEPOT-IOCL-PNP",
  setActiveDepot: () => {},
});

export const CPSE_OPTIONS = [
  { id: "IOCL", name: "Indian Oil Corporation Ltd", defaultDepot: "DEPOT-IOCL-PNP", defaultDepotName: "Panipat Refinery, Haryana" },
  { id: "ONGC", name: "Oil & Natural Gas Corporation", defaultDepot: "DEPOT-ONGC-HZR", defaultDepotName: "Hazira Gas Processing Plant, Gujarat" },
  { id: "BPCL", name: "Bharat Petroleum Corporation Ltd", defaultDepot: "DEPOT-BPCL-MUM", defaultDepotName: "Mumbai Refinery, Mahul, Maharashtra" },
  { id: "HPCL", name: "Hindustan Petroleum Corporation Ltd", defaultDepot: "DEPOT-HPCL-MUM", defaultDepotName: "Mumbai Refinery, Maharashtra" },
  { id: "GAIL", name: "GAIL (India) Limited", defaultDepot: "DEPOT-GAIL-PATA", defaultDepotName: "Pata Petrochemical Complex, UP" },
];

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [activeCpse, setActiveCpse] = useState<string>("IOCL");
  const [activeDepot, setActiveDepot] = useState<string>("DEPOT-IOCL-PNP");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const init = getInitialTheme();
    setTheme(init);
    applyTheme(init);

    const savedCpse = localStorage.getItem("samanvay_active_cpse");
    if (savedCpse) {
      setActiveCpse(savedCpse);
      const found = CPSE_OPTIONS.find((c) => c.id === savedCpse);
      if (found) setActiveDepot(found.defaultDepot);
    }

    setMounted(true);
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    applyTheme(nextTheme);
  };

  const handleSetCpse = (cpse: string) => {
    setActiveCpse(cpse);
    localStorage.setItem("samanvay_active_cpse", cpse);
    const found = CPSE_OPTIONS.find((c) => c.id === cpse);
    if (found) {
      setActiveDepot(found.defaultDepot);
      localStorage.setItem("samanvay_active_depot", found.defaultDepot);
    }
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        toggleTheme,
        activeCpse,
        setActiveCpse: handleSetCpse,
        activeDepot,
        setActiveDepot,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
