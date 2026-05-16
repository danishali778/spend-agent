import { PROMPT_BUNDLE_VERSION, PROMPT_SCHEMA_VERSIONS } from "./bundle.js";

const sourceReferenceSchema = {
  type: "object",
  additionalProperties: false,
  required: ["sourceDocumentId", "sourceSnippet", "confidenceScore"],
  properties: {
    sourceDocumentId: { type: "string", format: "uuid" },
    sourceSnippet: { type: "string", minLength: 1 },
    confidenceScore: { type: "number", minimum: 0, maximum: 1 },
  },
} as const;

export const promptBundleMetadata = {
  version: PROMPT_BUNDLE_VERSION,
  policy: {
    preferUnknownOverGuessing: true,
    requireProvenance: true,
    recommendEscalationOnInsufficientEvidence: true,
    hideRawChainOfThought: true,
  },
} as const;

export const documentAgentOutputSchema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "spendagent/document-agent-output",
  title: "DocumentAgentOutput",
  type: "object",
  additionalProperties: false,
  required: ["facts", "ambiguities", "missingCriticalFacts"],
  properties: {
    facts: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["factKey", "value", "sourceDocumentId", "sourceSnippet", "confidenceScore"],
        properties: {
          factKey: { type: "string", minLength: 1 },
          value: {
            anyOf: [
              { type: "string" },
              { type: "number" },
              { type: "boolean" },
              { type: "null" }
            ]
          },
          sourceDocumentId: sourceReferenceSchema.properties.sourceDocumentId,
          sourceSnippet: sourceReferenceSchema.properties.sourceSnippet,
          confidenceScore: sourceReferenceSchema.properties.confidenceScore
        }
      }
    },
    ambiguities: { type: "array", items: { type: "string" } },
    missingCriticalFacts: { type: "array", items: { type: "string" } }
  }
} as const;

export const financeAgentOutputSchema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "spendagent/finance-agent-output",
  title: "FinanceAgentOutput",
  type: "object",
  additionalProperties: false,
  required: ["usageSnapshot", "savingsScenarios", "conflicts"],
  properties: {
    usageSnapshot: {
      type: "object",
      additionalProperties: false,
      required: ["seatsPurchased", "seatsActive", "utilizationPercent", "totalCost", "costPeriod", "currency"],
      properties: {
        seatsPurchased: { type: ["integer", "null"], minimum: 0 },
        seatsActive: { type: ["integer", "null"], minimum: 0 },
        utilizationPercent: { type: ["number", "null"], minimum: 0, maximum: 100 },
        totalCost: { type: ["number", "null"], minimum: 0 },
        costPeriod: { type: ["string", "null"], enum: ["monthly", "annual", null] },
        currency: { type: ["string", "null"], minLength: 3, maxLength: 3 }
      }
    },
    savingsScenarios: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["action", "projectedSavings", "seatBaseline", "rationale"],
        properties: {
          action: { type: "string", enum: ["renew", "downgrade", "cancel", "renegotiate", "escalate"] },
          projectedSavings: { type: ["number", "null"], minimum: 0 },
          seatBaseline: { type: ["integer", "null"], minimum: 0 },
          rationale: { type: "string", minLength: 1 }
        }
      }
    },
    conflicts: { type: "array", items: { type: "string" } }
  }
} as const;

export const policyAgentOutputSchema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "spendagent/policy-agent-output",
  title: "PolicyAgentOutput",
  type: "object",
  additionalProperties: false,
  required: ["checks", "requiresEscalation"],
  properties: {
    checks: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["thresholdName", "result", "message"],
        properties: {
          thresholdName: { type: "string", minLength: 1 },
          result: { type: "string", enum: ["pass", "warn", "fail"] },
          message: { type: "string", minLength: 1 }
        }
      }
    },
    requiresEscalation: { type: "boolean" }
  }
} as const;

export const decisionAgentOutputSchema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "spendagent/decision-agent-output",
  title: "DecisionAgentOutput",
  type: "object",
  additionalProperties: false,
  required: [
    "recommendedAction",
    "confidenceScore",
    "rationale",
    "evidence",
    "projectedSavings",
    "blockers",
    "nextStep",
    "fallbackAction"
  ],
  properties: {
    recommendedAction: { type: "string", enum: ["renew", "downgrade", "cancel", "renegotiate", "escalate"] },
    confidenceScore: { type: "number", minimum: 0, maximum: 1 },
    rationale: { type: "string", minLength: 1 },
    evidence: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["factKey", "documentId", "snippet", "confidenceScore"],
        properties: {
          factKey: { type: "string", minLength: 1 },
          documentId: { type: "string", format: "uuid" },
          snippet: { type: "string", minLength: 1 },
          confidenceScore: { type: "number", minimum: 0, maximum: 1 }
        }
      }
    },
    projectedSavings: { type: ["number", "null"], minimum: 0 },
    blockers: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["code", "message"],
        properties: {
          code: { type: "string", minLength: 1 },
          message: { type: "string", minLength: 1 }
        }
      }
    },
    nextStep: { type: "string", minLength: 1 },
    fallbackAction: { type: ["string", "null"], enum: ["renew", "downgrade", "cancel", "renegotiate", "escalate", null] }
  }
} as const;

export const commsAgentOutputSchema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  $id: "spendagent/comms-agent-output",
  title: "CommsAgentOutput",
  type: "object",
  additionalProperties: false,
  required: ["artifacts"],
  properties: {
    artifacts: {
      type: "array",
      minItems: 1,
      items: {
        type: "object",
        additionalProperties: false,
        required: ["artifactType", "title", "content"],
        properties: {
          artifactType: { type: "string", enum: ["cfo_summary", "approval_note", "vendor_email"] },
          title: { type: "string", minLength: 1 },
          content: { type: "string", minLength: 1 }
        }
      }
    }
  }
} as const;

export const promptSchemas = {
  bundle: {
    version: promptBundleMetadata.version,
    policy: promptBundleMetadata.policy,
  },
  schemas: {
    documentAgent: {
      version: PROMPT_SCHEMA_VERSIONS.documentAgent,
      schema: documentAgentOutputSchema,
    },
    financeAgent: {
      version: PROMPT_SCHEMA_VERSIONS.financeAgent,
      schema: financeAgentOutputSchema,
    },
    policyAgent: {
      version: PROMPT_SCHEMA_VERSIONS.policyAgent,
      schema: policyAgentOutputSchema,
    },
    decisionAgent: {
      version: PROMPT_SCHEMA_VERSIONS.decisionAgent,
      schema: decisionAgentOutputSchema,
    },
    commsAgent: {
      version: PROMPT_SCHEMA_VERSIONS.commsAgent,
      schema: commsAgentOutputSchema,
    },
  },
} as const;
