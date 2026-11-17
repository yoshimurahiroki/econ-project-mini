# Writing

Writing expresses the adopted economic result from worksheet stages 1–6. Apply section 3 from the first visible message. Research judgment belongs to ECONOMIST and the task skill; this file governs expression, exemplars and form.

## The exemplar library

Use source wording throughout drafting and revision. The worksheet supplies the economic claims and evidence. Retrieve the expression needed at the current unit, copy its wording and syntax, and adapt economic names and actual quantities. Record source IDs and the copied expressions for each paragraph in the existing Exemplars used entry. Reuse the retrieved examples.

## 1. Borrow the argument from English originals

Use `exemplars.py borrow --lang en --level paragraph --query "<adopted finding or mechanism>"` for the argument's move and economic reasoning. For a document or section, `outline --lang en --doc DOC_ID` supplies the original sequence of paragraph claims. Use that sequence to organize the established answer. Economic claims and assumptions come from the worksheet.

## 2. Borrow Japanese wording while composing and revising

First state the paragraph's intended answer in the economic names used by the question. For a comparison, name both observations, choices or periods and the same outcome for each. Select one economic point that changes the requested judgment. Write it with verbs and complete clauses; technical labels and nested comparison nouns stay in the derivation. Query exemplars from this plain statement and borrow expression for that meaning.

Use the same retrieval tool at the unit being written:

| Unit | Source retrieval | Borrow |
|---|---|---|
| Vocabulary, phrases and expressions | `borrow --lang ja --level phrase --query "<actor and action>"` | Original collocation and its full sentence; noun–verb combination and particles |
| Sentences and syntax | `borrow --lang ja --level sentence --query "<economic relation>"` | Complete sentence, predicate, clause order, before/after context and connective |
| Paragraph | `borrow --lang ja --level paragraph --query "<judgment and economic reason>"` | The original claim, explanation and consequence in their order |
| Document or section | `outline --lang ja --doc DOC_ID` | Sequence of paragraph claims for the requested artifact |

1. Select a source paragraph expressing the plain judgment or mechanism and use its sentences to start `work/TOPIC-draft.md`. Read the returned full sentence and context before borrowing its language. Use economic objects and actions as query terms. Variable definitions serve requests for those definitions.
2. While writing each paragraph, retrieve any new technical compound noun, predicate and noun–verb combination. Use the user's established economic names. Adopt a new compound from an actual source or express its meaning as an ordinary clause. Batch several lookups in one command with repeated `--query`. Search terms co-occur in the returned sentence; use a simpler economic noun when a query returns no match. Compose from the retrieved phrases and sentence structure, using the actual adopted quantities and evidence.
3. During rewriting, search again at the changed unit. A new compound noun, predicate or noun–verb combination receives a phrase lookup; a changed subject–predicate–object relation receives a sentence lookup; a changed paragraph argument receives a paragraph lookup. Copy the returned wording with the same kind of subject, action and object. Adapt the actual actors and quantities while expressing the economic relationship established in the worksheet. Reuse unchanged source expressions.
4. Complete the existing finish pass from the original question: a reader using its named objects can identify the two sides of every comparison, the outcome and the resulting action or finding. Replace compressed noun chains with those complete clauses. Delete extra concepts that only extend methodological discussion, including warnings about claims or interpretations absent from the request. Remove these topics from the answer rather than distributing them across additional paragraphs. Check whole-sentence meaning and source wording in that same pass. Read each sentence as an assertion: name who or what acts, the action or comparison, its object and the resulting finding. Rewrite the sentence as that plain assertion using the task's economic names. Delete sentences that only announce interpretation, scope or further analysis. Read technical compounds with their predicates and resolve abstract pronouns to their actual objects. Compare that meaning with the adopted worksheet result and the source's full sentence. Record the source IDs and copied expressions for each paragraph in Exemplars used; remove source comments from the public draft. Submit the edited file to `write-answer` through stdin. A marked passage follows the same local lookup and editing procedure.

Run retrieval sequentially. Papers use 「，．」, conversational answers 「、。」; slides follow the selected originals.

## 3. Expression rules

**All-stage record.** Apply direct-claim and anti-defensive rules to every worksheet entry and visible message. Use affirmative clauses from the first message. State the adopted result, concrete specification or completed correction and its economic consequence directly. Each public sentence advances the answer to the original question, its derived economic mechanism or an actual saved numerical result. A premise or specification earns space through a substantive change in the economic judgment. State the adopted comparison and consequence directly; omit prerequisite announcements, added-premise plans and routine reporting promises. Use ECONOMIST Economic priority and Requested work from the first stage. Give the requested result directly; routine sensitivity work, assumption checks and procedure explanations stay outside the deliverable unless explicitly requested. Record the strongest adopted conclusion and determining reason before drafting. Omit self-evident premises and objective-restatement boundaries; choice answers explain the decisive economic settings and select one action. Keep calculation-status notes, generic cautions and supplementary work in the worksheet. Before drafting, read the block rules in quality/prose_rules.json once. Select public content from the substantive judgment and its decisive economic reason. Delete sentences devoted only to routine conditions, definitions or implementation; use the source-backed result and actual quantities. Before expression, state the answer to the actual submitted claim or proposed operation, using the user's economic names with both sides of the comparison and one determining reason. For Japanese, use exemplars.py borrow while composing and rewriting: look up new compound nouns and predicates, copy source wording with its subject–action–object relationship, and read the whole sentence as a plain economic assertion, and submit the edited working file to the writer. Progress gives the concrete operation or saved finding.

1. Use affirmative predicates. State what the comparison identifies, what the adopted specification does and which action follows. Express a detected error as its exact corrected result or replacement. Preserve scientific meaning by choosing the concrete supported claim. Lead with the answer. A recommendation states the adopted action and its economic intuition. A review states its strongest derived conclusion and the economic reason that establishes it. A quantitative request receives the quantity and its specification. Deliver the requested artifact itself.
2. Preserve evidence and numerical uncertainty. Each number retains its source, population, unit and saved interval. Present computed values themselves. Routine statements promising a confidence interval, standard error or estimate belong in the worksheet. A design review leads with its strongest substantive judgment and the economic derivation that establishes it. Use precise work-specific names and specification labels; standard methods and software need their names. The result's actual scope and evidence determine the claim.
3. For Japanese, retrieve and copy wording at the unit being composed or changed under section 2: vocabulary, phrase, sentence, paragraph or document. Adapt economic names and quantities to the adopted finding and use the original predicates, particles and clause structure. Complete the existing finish pass against the source expressions used in each paragraph. For choice requests, name the contrasting economic settings, explain their induced behavior and different recommendations, then adopt one action under ECONOMIST Selecting an action. Omit self-evident premises and boundaries that merely restate the objective. Keep derivation details and measurement plans in the worksheet.
4. Remove hedges, disclaimers, concessions, defensive framing, negation contrasts, ornament, vague value judgments, deferrals and supplementary notes. Examples convey the result with the same force; remove prefaces that downgrade it to mere illustration. Replace an evasive sentence with the supported action or finding while preserving its evidence and meaning. A mixture or allocation follows the solved objective.

## 4. Form

Use the [Japanese](../profiles/academic-ja/PROFILE.md) or [English](../profiles/top-five-en/PROFILE.md) profile for document form and the matching template in `tex/`. A conversation follows the user's requested length. Profiles and templates specify presentation.

## 5. Finish

1. Complete the worksheet headings, knowledge IDs, expression entry and closing header before committing the adopted result. Commit the completed worksheet: `python3 hooks/check.py commit-decision work/TOPIC.md`. Save the complete official body through:

   ```sh
   python3 hooks/check.py write-answer work/TOPIC.md < work/TOPIC-draft.md
   ```

2. The existing write-answer scans the body before saving, using the block rules in quality/prose_rules.json. A marked passage returns for content selection and affirmative expression. Delete a passage devoted only to a standard definition, routine condition or implementation detail. Look up each changed predicate or noun–verb combination with borrow --level phrase and changed logical relations with --level sentence. Edit the working file with the returned source wording, adapting economic names and actual quantities. Submit that complete edited file through write-answer. Its drafted status confirms the saved body passed those lexical rules. Read the body once for whole-sentence meaning and source wording: state each actor, action, object and economic consequence in plain Japanese. Remove meta statements that merely announce scope or interpretation. Deliver that corrected body. A changed adopted result receives a new commit.
3. Use Status: closed, Current step: 7, Next action: none for completed work; continuing work uses open and its next action. Return the complete saved body. After a record-only repair, return that complete body again. Keep worksheet administration internal.
4. For artifacts, read changed rendered pages and repair concrete errors at their source.
