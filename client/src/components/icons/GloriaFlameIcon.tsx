import { SvgIcon, type SvgIconProps } from "@mui/material";

/**
 * Apollo side profile (head to shoulders) with a torch held in front,
 * flame visible near the face. Gloria Trade brand icon.
 */
export default function GloriaFlameIcon(props: SvgIconProps) {
  return (
    <SvgIcon {...props} viewBox="0 0 24 24">
      {/* Flame */}
      <path d="M18.5 2c0 0-2 1.8-2 3.5c0 1.1.9 2 2 2s2-.9 2-2C20.5 3.8 18.5 2 18.5 2z" />
      <path
        d="M17.8 4c0-.5.2-.9.4-1.2c-.2-.1-.4-.2-.6-.2c-.8 0-1.3.7-1.3 1.5c0 .5.4 1 1 1c.2 0 .4-.1.5-.2c-.1-.2-.1-.5 0-.9z"
        opacity={0.45}
      />

      {/* Torch handle — vertical in front of face */}
      <rect x="17.8" y="7.2" width="1.4" height="9" rx="0.5" />
      {/* Torch cup */}
      <path d="M17.2 7.2h2.6l-.3.8h-2z" />

      {/* Apollo head — side profile facing right */}
      <path
        d="M13.5 6.5
           c0-2.5-1.8-4-4-4
           c-2.5 0-4.2 1.8-4.2 4.2
           c0 1.5.6 2.5 1.5 3.2
           l-.3 1.2
           l1.8-.4
           c.5.2 1 .3 1.5.3
           c2.8 0 3.7-2 3.7-4.5z"
      />

      {/* Laurel wreath on head */}
      <path
        d="M6 4.5c.3-.8 1-1.2 1.5-.8c-.2.5-.7.8-1.5.8z
           M6.5 3.5c.5-.6 1.2-.7 1.5-.3c-.3.4-.9.5-1.5.3z
           M7.5 2.8c.6-.4 1.2-.3 1.4.1c-.4.3-1 .3-1.4-.1z"
        opacity={0.5}
      />

      {/* Neck */}
      <path d="M9 11l-1 1.5l3.5 0l-.5-1.5z" />

      {/* Shoulders / upper chest drape */}
      <path
        d="M3 20
           c0-3 1.5-5.5 4-6.5
           l1-1
           l4.5 0
           l1 1
           c2.5 1 4 3.5 4 6.5
           z"
      />

      {/* Toga drape line across chest */}
      <path
        d="M5 17c1.5-2 3.5-3 6-3.2"
        fill="none"
        stroke="currentColor"
        strokeWidth="0.6"
        opacity={0.25}
      />

      {/* Hand holding torch */}
      <ellipse cx="18" cy="16.5" rx="1.2" ry="0.9" transform="rotate(-10 18 16.5)" opacity={0.7} />
      {/* Forearm reaching to torch */}
      <path
        d="M14.5 14.5c1.5 0 2.5.8 3.2 1.8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </SvgIcon>
  );
}
