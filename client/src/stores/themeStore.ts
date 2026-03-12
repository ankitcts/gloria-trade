import { create } from "zustand";
import { persist } from "zustand/middleware";

type ThemeMode = "light" | "dark";

interface ThemeStore {
  mode: ThemeMode;
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      mode: "dark" as ThemeMode,
      toggleTheme: () =>
        set((state) => ({
          mode: state.mode === "dark" ? "light" : "dark",
        })),
    }),
    {
      name: "gloria-theme",
    }
  )
);
