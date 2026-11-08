import { useId, type ReactNode } from "react";

import { Icon } from "./Icon";

// Info icon with a hover/focus bubble; the text is also the accessible description.
export function InfoTip({ text }: { text: ReactNode }) {
  const id = useId();
  return (
    <span className="tip" tabIndex={0} aria-describedby={id}>
      <Icon name="info" />
      <span role="tooltip" id={id} className="tip__bubble">{text}</span>
    </span>
  );
}
