import { flow, manual, connector, inlineAgent, lookup, js, tmpl, out, v, lit, types } from "@uipath/maestro-builder-sdk";

const GMAIL = { connection: "gmail", folder: "shared" } as const;
const JIRA = { connection: "jira", folder: "shared" } as const;
const SLACK = { connection: "slack", folder: "shared" } as const;

// The Gmail "Email Received" trigger (emailReceivedInbox1) and the attachment download step
// (downloadAttachment1) are added to the emitted .flow with `uip maestro flow node add`
// after the last compile — see the repo's AGENTS.md. Expressions below read them by id.
const MESSAGE_ID = js`$vars.start?.output?.messageId || $vars["emailReceivedInbox1"]?.output?.ID`;

const issueFields = (workType: string) => ({
  fields: {
    project: { key: lookup("uipath-atlassian-jira", "create-issue", "fields.project.key").by("name", "Support") },
    issuetype: { id: lookup("uipath-atlassian-jira", "create-issue", "fields.issuetype.id").by("name", workType) },
    summary: js`$vars.getEmail.output.Subject || "(no subject)"`,
    description: tmpl`From: ${js`$vars.getEmail.output.From.Name`} <${js`$vars.getEmail.output.From.Email`}>

Summary: ${out("classify", "summary")}

${js`$vars.getEmail.output.Body`}`,
  },
});

const fileTicket = (step: string, workType: string) =>
  connector("uipath-atlassian-jira", "create-issue", issueFields(workType), JIRA);

export default flow("12fa0c85-f5d3-4f9d-8518-ef0431a60a57")
  .schemaVersion("1.9")
  .name("SupportInbox")
  .input({ messageId: types.string })
  .output({ category: types.string, replyText: types.string, refundRequested: types.boolean })
  .var("ticketKey", types.string, "")
  .trigger(manual(), { version: "1.0" })

  .step("getEmail", connector("uipath-google-gmail", "get-email-by-id", { id: MESSAGE_ID }, GMAIL))

  .step(
    "classify",
    inlineAgent({
      model: "claude-sonnet-5-5",
      systemPrompt: [
        "You triage emails sent to a software company's customer support inbox.",
        "Use only the sender, subject and body you are given.",
        "Return a result conforming to the output schema:",
        "- category: exactly one of billing | bug | how-to | other | spam.",
        "  billing = charges, invoices, refunds, plans, payment. bug = the product is broken or behaves wrongly.",
        "  how-to = the customer asks how to do something with the product. spam = unsolicited marketing, phishing, scams or mail not meant for support.",
        "  other = a genuine customer email that fits none of the above.",
        "- summary: one or two sentences for the support team describing what the customer wants.",
        "- replyText: a short, polite reply to the customer, signed 'Support team'. Acknowledge the request and say what happens next. Do not promise refunds, credits or fixes. For spam, return an empty string.",
        "- refundRequested: true only if the customer explicitly asks for a refund or money back; otherwise false.",
      ].join("\n"),
      userPrompt: "From: {{input.fromName}} <{{input.fromEmail}}>\nSubject: {{input.subject}}\n\n{{input.body}}",
      inputs: {
        fromName: js`$vars.getEmail.output.From.Name`,
        fromEmail: js`$vars.getEmail.output.From.Email`,
        subject: js`$vars.getEmail.output.Subject`,
        body: js`$vars.getEmail.output.Body`,
      },
      returns: { category: "string", summary: "string", replyText: "string", refundRequested: "boolean" },
    }),
  )

  .switch("byCategory", out("classify", "category"), [
    { value: "billing", label: "Billing", body: (b) => b.step("ticketBilling", fileTicket("ticketBilling", "Billing"), { updates: { ticketKey: out("ticketBilling", "key") } }) },
    { value: "bug", label: "Bug", body: (b) => b.step("ticketBug", fileTicket("ticketBug", "Bug"), { updates: { ticketKey: out("ticketBug", "key") } }) },
    { value: "how-to", label: "How-to", body: (b) => b.step("ticketHowTo", fileTicket("ticketHowTo", "How-To"), { updates: { ticketKey: out("ticketHowTo", "key") } }) },
    { value: "spam", label: "Spam", body: (b) => b.step("ticketSpam", fileTicket("ticketSpam", "Spam"), { updates: { ticketKey: out("ticketSpam", "key") } }) },
  ], (other) => other.step("ticketOther", fileTicket("ticketOther", "Other"), { updates: { ticketKey: out("ticketOther", "key") } }))

  .branch("hasAttachments", js`$vars.getEmail.output.HasAttachments === true`, (yes) =>
    yes.label("Has attachments").loop("eachAttachment", js`$vars.getEmail.output.Attachments`, (body) =>
      body.step(
        "attachToTicket",
        connector("uipath-atlassian-jira", "add-issue-attachment", {
          issueIdOrKey: v("ticketKey"),
          file: js`$vars["downloadAttachment1"].output`,
        }, JIRA),
      ),
    ),
  )

  .branch("notSpam", js`$vars.classify.output.category !== "spam"`, (yes) =>
    yes
      .label("Not spam")
      .step("jiraSite", connector("uipath-atlassian-jira", "get-instance-details", {}, JIRA))
      .step(
        "postSlack",
        connector("uipath-salesforce-slack", "send-message-to-channel", {
          channel: lookup("uipath-salesforce-slack", "send-message-to-channel", "channel").by("name", "support"),
          send_as: lookup("uipath-salesforce-slack", "send-message-to-channel", "send_as").by("name", "Bot"),
          messageToSend: tmpl`*New ${out("classify", "category")} email* from ${js`$vars.getEmail.output.From.Email`}: ${js`$vars.getEmail.output.Subject`}
${out("classify", "summary")}
Ticket: <${out("jiraSite", "baseUrl")}/browse/${v("ticketKey")}|${v("ticketKey")}>`,
        }, SLACK),
      )
      .step(
        "draftReply",
        connector("uipath-google-gmail", "reply-to-email", {
          id: js`$vars.getEmail.output.ID`,
          body: out("classify", "replyText"),
          saveAsDraft: lit(true),
        }, GMAIL),
      ),
  )

  .step("markRead", connector("uipath-google-gmail", "mark-email-as-read-or-unread", { id: js`$vars.getEmail.output.ID`, markAs: "read" }, GMAIL))

  .return({
    category: out("classify", "category"),
    replyText: out("classify", "replyText"),
    refundRequested: out("classify", "refundRequested"),
  })
  .build();
