import type { ReactNode } from "react";

export function PageHeader({ title, description, actions }: { title: ReactNode; description?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="page-header">
      <div><h1>{title}</h1>{description ? <p>{description}</p> : null}</div>
      {actions ? <div className="row">{actions}</div> : null}
    </div>
  );
}
