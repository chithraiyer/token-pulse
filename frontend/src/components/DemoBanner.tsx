import { useMeta } from "../api/hooks";

// FR-004: make it unmistakable when the dashboard is running on synthetic data.
export function DemoBanner() {
  const { data } = useMeta();
  if (!data?.is_demo_data) return null;
  return (
    <div role="status" className="demo-banner">
      Synthetic demo data — not real usage. Mode: <code>{data.mode}</code> · rules{" "}
      <code>{data.rule_catalog_version}</code> · pricing{" "}
      <code>{data.pricing_table_versions.join(", ")}</code>
    </div>
  );
}
