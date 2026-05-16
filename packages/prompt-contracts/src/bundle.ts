import type { PromptBundleVersion } from "@spendagent/shared-types";

export const PROMPT_BUNDLE_VERSION: PromptBundleVersion = "v1.0.0";

export const PROMPT_SCHEMA_VERSIONS = {
  documentAgent: "1.0.0",
  financeAgent: "1.0.0",
  policyAgent: "1.0.0",
  decisionAgent: "1.0.0",
  commsAgent: "1.0.0",
} as const;
