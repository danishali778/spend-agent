import assert from "node:assert/strict";
import test from "node:test";

import contracts from "../src/public-contracts.json" with { type: "json" };
import promptSchemas from "../../prompt-contracts/src/schemas.json" with { type: "json" };
import fixture from "../../../supabase/seed/fixtures/acme-pm-suite.json" with { type: "json" };

const getMissingKeys = (value, keys) => keys.filter((key) => !(key in value));

test("fixture public view models match documented shared contracts", () => {
  assert.deepEqual(
    getMissingKeys(fixture.caseSummary, contracts.interfaces.CaseSummary),
    [],
  );
  assert.deepEqual(
    getMissingKeys(fixture.decisionPacket, contracts.interfaces.DecisionPacket),
    [],
  );
  fixture.generatedArtifacts.forEach((artifact) => {
    assert.deepEqual(
      getMissingKeys(artifact, contracts.interfaces.GeneratedArtifact),
      [],
    );
    assert.ok(
      contracts.enums.artifactType.includes(artifact.artifactType),
      `unexpected artifact type ${artifact.artifactType}`,
    );
  });
  fixture.activityTimeline.forEach((event) => {
    assert.deepEqual(
      getMissingKeys(event, contracts.interfaces.AgentActivityEvent),
      [],
    );
    assert.ok(
      contracts.enums.stepStatus.includes(event.status),
      `unexpected step status ${event.status}`,
    );
  });
});

test("fixture decisions and artifacts line up with prompt contract versioning", () => {
  assert.equal(fixture.promptBundleVersion, promptSchemas.bundle.version);
  assert.equal(fixture.db.agent_runs[0].prompt_bundle_version, promptSchemas.bundle.version);
  assert.equal(fixture.db.decisions[0].recommended_action, fixture.decisionPacket.recommendedAction);
  assert.equal(fixture.db.decisions[0].fallback_action, fixture.decisionPacket.fallbackAction);
  assert.equal(fixture.db.generated_artifacts.length, fixture.generatedArtifacts.length);
});

test("fixture enums stay within the canonical vocabulary", () => {
  const caseRecord = fixture.db.cases[0];
  assert.ok(contracts.enums.caseStatus.includes(caseRecord.status));
  assert.ok(contracts.enums.urgencyLevel.includes(caseRecord.urgency_level));
  assert.ok(contracts.enums.recommendedAction.includes(fixture.decisionPacket.recommendedAction));
  fixture.db.documents.forEach((document) => {
    assert.ok(contracts.enums.documentType.includes(document.type));
    assert.ok(contracts.enums.parseStatus.includes(document.parse_status));
  });
});
