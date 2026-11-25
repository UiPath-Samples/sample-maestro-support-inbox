// @decompiled-from SupportInbox.flow sha256:7c2f228c60d355d99184cf81acee08b8c637c9adb6e4377930de7dc52969e7df scripts=function fetch
import { connector, flow, inlineAgent, js, manual, out, script, types, v, type FlowVars } from "@uipath/maestro-builder-sdk";

const switchV1_4Definition = {
  "nodeType": "core.logic.switch",
  "version": "1.4",
  "category": "control-flow",
  "description": "Route to one or more branches by condition",
  "tags": [
    "control-flow",
    "switch",
    "case",
    "when"
  ],
  "sortOrder": 62,
  "display": {
    "label": "Switch",
    "icon": "between-horizontal-start"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        }
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "case-{item.id}",
          "type": "source",
          "handleType": "output",
          "label": "{item.label || 'Case ' + (index + 1)}",
          "repeat": "inputs.cases"
        },
        {
          "id": "default",
          "type": "source",
          "handleType": "output",
          "label": "{inputs.defaultBranch.label}",
          "visible": "{inputs.cases.length === 0 || inputs.defaultBranch.enabled !== false}"
        }
      ],
      "visible": true
    }
  ],
  "debug": {
    "runtime": "clientScript"
  },
  "model": {
    "type": "bpmn:ExclusiveGateway"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "cases": {
        "type": "array",
        "minItems": 1,
        "errorMessage": "At least one case is required",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string"
            },
            "label": {
              "type": "string"
            },
            "expression": {
              "type": "string",
              "minLength": 1,
              "errorMessage": "Add a condition"
            }
          },
          "required": [
            "expression"
          ]
        }
      },
      "defaultBranch": {
        "type": "object",
        "properties": {
          "enabled": {
            "type": "boolean"
          },
          "label": {
            "type": "string"
          }
        }
      },
      "matchAllCases": {
        "type": "boolean"
      }
    },
    "required": [
      "cases"
    ]
  },
  "outputDefinition": {},
  "inputDefaults": {
    "cases": [
      {
        "id": "default-1",
        "label": "Case 1",
        "expression": ""
      },
      {
        "id": "default-2",
        "label": "Case 2",
        "expression": ""
      }
    ],
    "defaultBranch": {
      "enabled": true,
      "label": "Default"
    },
    "matchAllCases": false
  },
  "form": {
    "id": "switch-properties",
    "title": "Switch configuration",
    "sections": [
      {
        "id": "cases",
        "title": "Cases",
        "description": "Cases are evaluated in order.",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.cases",
            "type": "custom",
            "label": "Switch cases",
            "component": "case-list-editor",
            "componentProps": {
              "defaultBranchRow": true,
              "minCases": 1,
              "maxCases": 10,
              "expressionPlaceholder": "$vars.httpRequest1.output.statusCode >= 200 && $vars.httpRequest1.output.statusCode < 300",
              "expressionValidationFields": [
                {
                  "subPath": "expression",
                  "validationMode": "expression",
                  "expectedType": "boolean"
                }
              ]
            }
          },
          {
            "name": "inputs.matchAllCases",
            "type": "switch",
            "label": "Match all cases",
            "description": "The flow continues down every case whose condition is true, not only the first.",
            "defaultValue": false
          }
        ]
      }
    ]
  },
  "runtimeConstraints": {
    "exclude": [
      "api-function"
    ]
  }
};

const decisionV1_4Definition = {
  "nodeType": "core.logic.decision",
  "version": "1.4",
  "category": "control-flow",
  "description": "Branch on a true or false condition",
  "tags": [
    "control-flow",
    "if",
    "loop",
    "switch"
  ],
  "sortOrder": 61,
  "display": {
    "label": "Decision",
    "icon": "trending-up-down"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        }
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "true",
          "type": "source",
          "handleType": "output",
          "label": "{inputs.trueLabel}"
        },
        {
          "id": "false",
          "type": "source",
          "handleType": "output",
          "label": "{inputs.falseLabel}"
        }
      ],
      "visible": true
    }
  ],
  "debug": {
    "runtime": "clientScript"
  },
  "model": {
    "type": "bpmn:InclusiveGateway"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "expression": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "Add a condition"
      },
      "trueLabel": {
        "type": "string"
      },
      "falseLabel": {
        "type": "string"
      }
    },
    "required": [
      "expression"
    ]
  },
  "outputDefinition": {},
  "inputDefaults": {
    "trueLabel": "True",
    "falseLabel": "False"
  },
  "form": {
    "id": "decision-properties",
    "title": "Decision configuration",
    "sections": [
      {
        "id": "condition",
        "title": "Condition",
        "fields": [
          {
            "name": "inputs.expression",
            "type": "custom",
            "component": "code-editor",
            "componentProps": {
              "singleLine": true,
              "mode": "expression",
              "toggleable": false,
              "language": "javascript",
              "returnType": "boolean",
              "validationMode": "expression",
              "showVariableButton": true,
              "placeholder": "$vars.httpRequest1.output.statusCode >= 200 && $vars.httpRequest1.output.statusCode < 300"
            },
            "label": "Condition",
            "description": "The condition must be a JavaScript expression that evaluates to true or false."
          },
          {
            "name": "inputs.trueLabel",
            "type": "text",
            "label": "True branch label",
            "description": "This label appears on the true branch."
          },
          {
            "name": "inputs.falseLabel",
            "type": "text",
            "label": "False branch label",
            "description": "This label appears on the false branch."
          }
        ]
      }
    ]
  }
};

export default flow("6e7b40f8-6c5a-4e56-86f0-9475c79b1866")
  .schemaVersion("1.9")
  .name("SupportInbox")
  .definitions([switchV1_4Definition, decisionV1_4Definition])
  .openTails()
  .input({ messageId: types.string })
  .output({ category: types.string, replyText: types.string, refundRequested: types.boolean })
  .var("ticketKey", types.string, "")
  .var("downloadedFiles", types.array, [])
  .trigger(manual(), { version: "1.0" })
  .step("getEmail", connector("uipath-google-gmail", "get-email-by-id", { id: js`$vars.start?.output?.messageId || $vars["emailReceivedInbox1"]?.output?.ID` }, { connection: "593b14fc-f445-4c6a-89b7-016833566cab", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0" })
  .branch("hasAttachments", js`$vars.getEmail.output.HasAttachments === true`,
    (t) => t
      .label("Has attachments")
      .loop("eachAttachment", out("getEmail", "Attachments"), (b) => b
        .step("downloadAttachment1", connector("uipath-google-gmail", "download-email-attachment-by-attachment-id", { excludeInlineAttachment: false, id: js`($vars.eachAttachment.currentItem.ID)` }, { connection: "593b14fc-f445-4c6a-89b7-016833566cab", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0", label: "Download attachment" })
        .step("collectAttachment", script(collectAttachment, { returns: { files: "array" } }), { updates: { downloadedFiles: out("collectAttachment", "files") } }), { version: "2.4" }),
    (e) => e, { version: "1.4" })
  .step("prepareFiles", script(prepareFiles, { returns: { attachments: "array", attachmentList: "string", otherAttachments: "string" } }))
  .step("classify", inlineAgent({ model: "claude-sonnet-5-5", systemPrompt: "You triage emails sent to a software company's customer support inbox.\nUse the sender, subject and body you are given, and the email's PDF and image attachments when it has any.\n\nAttachments: the user message lists each PDF or image attachment with its ID, FullName and MimeType. When that list is not \"(none)\", call the Analyze Files tool on those attachments, passing each attachment's ID exactly as it is listed, and read them to extract the customer's account ID, the amount (with its currency) and any error code. Never make up an attachment ID, and do not call the tool when the list is \"(none)\". Other attachments are listed by name only and are not read.\nUse what you extract, together with the email itself, to decide the category and to write the reply. For example, an invoice or receipt that shows a charge points to billing, and a screenshot that shows an error code points to bug.\n\nReturn a result conforming to the output schema:\n- category: exactly one of billing | bug | how-to | other | spam.\n  billing = charges, invoices, refunds, plans, payment. bug = the product is broken or behaves wrongly.\n  how-to = the customer asks how to do something with the product. spam = unsolicited marketing, phishing, scams or mail not meant for support.\n  other = a genuine customer email that fits none of the above.\n- summary: one or two sentences for the support team describing what the customer wants. Include the account ID, amount and error code you found, when there are any.\n- replyText: a short, polite reply to the customer, signed 'Support team'. Acknowledge the request and say what happens next. When you found an account ID, amount or error code, refer to it so the customer knows it was read. Do not promise refunds, credits or fixes. For spam, return an empty string.\n- refundRequested: true only if the customer explicitly asks for a refund or money back; otherwise false.\n- accountId: the customer's account ID from the email or its attachments, or an empty string if there is none.\n- amount: the amount from the email or its attachments, with its currency, or an empty string if there is none.\n- errorCode: the error code from the email or its attachments, or an empty string if there is none.", userPrompt: "From: {{input.getEmail__output__From__Name}} <{{input.getEmail__output__From__Email}}>\nSubject: {{input.getEmail__output__Subject}}\n\n{{input.getEmail__output__Body}}\n\nPDF and image attachments to read with the Analyze Files tool (ID, FullName, MimeType):\n{{input.prepareFiles__output__attachmentList}}\n\nAttachment files: {{input.prepareFiles__output__attachments}}\n\nOther attachments (not read): {{input.prepareFiles__output__otherAttachments}}", inputs: { getEmail__output__From__Name: out("getEmail", "From.Name"), getEmail__output__From__Email: out("getEmail", "From.Email"), getEmail__output__Subject: out("getEmail", "Subject"), getEmail__output__Body: out("getEmail", "Body"), prepareFiles__output__attachmentList: out("prepareFiles", "attachmentList"), prepareFiles__output__attachments: out("prepareFiles", "attachments"), prepareFiles__output__otherAttachments: out("prepareFiles", "otherAttachments") }, returns: { category: "string", summary: "string", replyText: "string", refundRequested: "boolean", accountId: "string", amount: "string", errorCode: "string" }, tools: [{ kind: "builtin", tool: "analyzefiles" }], temperature: 1, maxTokenPerResponse: 16384, maxIterations: 25, mode: "standard", source: "0174c276-fdb5-4b4e-bbb6-599f9aa148f8" }), { version: "1.4" })
  .switch("byCategory", out("classify", "category"), [
    { value: "billing", label: "Billing", body: (b) => b
      .step("ticketBilling", connector("uipath-atlassian-jira", "create-issue", { "fields.project.key": "SUP", "fields.issuetype.id": "10009", "fields.summary": js`($vars.getEmail.output.Subject || "(no subject)")`, "fields.description": js`(\`From: \${$vars.getEmail.output.From.Name} <\${$vars.getEmail.output.From.Email}>

Summary: \${$vars.classify.output.summary}

\${$vars.getEmail.output.Body}\`)` }, { connection: "3a1fd879-252e-4f03-a20d-1a5a5ee539ef", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0", updates: { ticketKey: out("ticketBilling", "key") } }) },
    { value: "bug", label: "Bug", body: (b) => b
      .step("ticketBug", connector("uipath-atlassian-jira", "create-issue", { "fields.project.key": "SUP", "fields.issuetype.id": "10008", "fields.summary": js`($vars.getEmail.output.Subject || "(no subject)")`, "fields.description": js`(\`From: \${$vars.getEmail.output.From.Name} <\${$vars.getEmail.output.From.Email}>

Summary: \${$vars.classify.output.summary}

\${$vars.getEmail.output.Body}\`)` }, { connection: "3a1fd879-252e-4f03-a20d-1a5a5ee539ef", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0", updates: { ticketKey: out("ticketBug", "key") } }) },
    { value: "how-to", label: "How-to", body: (b) => b
      .step("ticketHowTo", connector("uipath-atlassian-jira", "create-issue", { "fields.project.key": "SUP", "fields.issuetype.id": "10010", "fields.summary": js`($vars.getEmail.output.Subject || "(no subject)")`, "fields.description": js`(\`From: \${$vars.getEmail.output.From.Name} <\${$vars.getEmail.output.From.Email}>

Summary: \${$vars.classify.output.summary}

\${$vars.getEmail.output.Body}\`)` }, { connection: "3a1fd879-252e-4f03-a20d-1a5a5ee539ef", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0", updates: { ticketKey: out("ticketHowTo", "key") } }) },
    { value: "spam", label: "Spam", body: (b) => b
      .step("ticketSpam", connector("uipath-atlassian-jira", "create-issue", { "fields.project.key": "SUP", "fields.issuetype.id": "10012", "fields.summary": js`($vars.getEmail.output.Subject || "(no subject)")`, "fields.description": js`(\`From: \${$vars.getEmail.output.From.Name} <\${$vars.getEmail.output.From.Email}>

Summary: \${$vars.classify.output.summary}

\${$vars.getEmail.output.Body}\`)` }, { connection: "3a1fd879-252e-4f03-a20d-1a5a5ee539ef", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0", updates: { ticketKey: out("ticketSpam", "key") } }) },
  ], (d) => d
    .step("ticketOther", connector("uipath-atlassian-jira", "create-issue", { "fields.project.key": "SUP", "fields.issuetype.id": "10011", "fields.summary": js`($vars.getEmail.output.Subject || "(no subject)")`, "fields.description": js`(\`From: \${$vars.getEmail.output.From.Name} <\${$vars.getEmail.output.From.Email}>

Summary: \${$vars.classify.output.summary}

\${$vars.getEmail.output.Body}\`)` }, { connection: "3a1fd879-252e-4f03-a20d-1a5a5ee539ef", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0", updates: { ticketKey: out("ticketOther", "key") } }), { version: "1.4" })
  .branch("hasFilesToAttach", js`($vars.downloadedFiles || []).length > 0`,
    (t) => t
      .label("Files to attach")
      .loop("eachDownloadedFile", v("downloadedFiles"), (b) => b
        .step("attachToTicket", connector("uipath-atlassian-jira", "add-issue-attachment", { issueIdOrKey: js`($vars.ticketKey)`, file: js`($vars.eachDownloadedFile.currentItem)` }, { connection: "3a1fd879-252e-4f03-a20d-1a5a5ee539ef", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0" }), { version: "2.4" }),
    (e) => e, { version: "1.4" })
  .branch("notSpam", js`$vars.classify.output.category !== "spam"`,
    (t) => t
      .label("Not spam")
      .step("jiraSite", connector("uipath-atlassian-jira", "get-instance-details", {}, { connection: "3a1fd879-252e-4f03-a20d-1a5a5ee539ef", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0" })
      .step("postSlack", connector("uipath-salesforce-slack", "send-message-to-channel", { channel: "C0CKRS6HY73", messageToSend: js`\`*New \${$vars.classify.output.category} email* from \${$vars.getEmail.output.From.Email}: \${$vars.getEmail.output.Subject}
\${$vars.classify.output.summary}
Ticket: <\${$vars.jiraSite.output.baseUrl}/browse/\${$vars.ticketKey}|\${$vars.ticketKey}>\``, send_as: "bot" }, { connection: "5ad1820c-70e9-4750-b25e-e2cd028b6c7f", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0" })
      .step("draftReply", connector("uipath-google-gmail", "reply-to-email", { body: out("classify", "replyText"), id: out("getEmail", "ID"), saveAsDraft: true }, { connection: "593b14fc-f445-4c6a-89b7-016833566cab", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0" }),
    (e) => e, { version: "1.4" })
  .step("markRead", connector("uipath-google-gmail", "mark-email-as-read-or-unread", { id: out("getEmail", "ID"), markAs: "read" }, { connection: "593b14fc-f445-4c6a-89b7-016833566cab", folder: "e52f05df-eac6-4f5e-b25d-ebd56830d665" }), { version: "1.0.0" })
  .return({ category: out("classify", "category"), replyText: out("classify", "replyText"), refundRequested: out("classify", "refundRequested") }, { version: "1.0" })
  .stickyNotes([
    { id: "sticky-1", content: "Classify incoming email", color: "green", x: 832, y: -1008, width: 784, height: 208 },
    { id: "sticky-2", content: "Create Jira ticket and attach files", color: "blue", x: 672, y: -784, width: 1504, height: 432 },
    { id: "sticky-3", content: "Notify team (Slack) and customer (email)", x: 1216, y: -320, width: 480, height: 192 },
  ])
  .layout({
    nodes: {
      start: { position: { x: 544, y: -1088 }, size: { width: 96, height: 96 }, collapsed: false },
      getEmail: { position: { x: 880, y: -944 }, size: { width: 96, height: 96 }, collapsed: false },
      classify: { position: { x: 1296, y: -944 }, size: { width: 288, height: 96 }, collapsed: false },
      byCategory: { position: { x: 704, y: -672 }, size: { width: 96, height: 192 }, collapsed: false },
      ticketBilling: { position: { x: 928, y: -784 }, size: { width: 96, height: 96 }, collapsed: false },
      ticketBug: { position: { x: 1056, y: -704 }, size: { width: 96, height: 96 }, collapsed: false },
      ticketHowTo: { position: { x: 1168, y: -624 }, size: { width: 96, height: 96 }, collapsed: false },
      ticketSpam: { position: { x: 1056, y: -544 }, size: { width: 96, height: 96 }, collapsed: false },
      ticketOther: { position: { x: 928, y: -464 }, size: { width: 96, height: 96 }, collapsed: false },
      hasAttachments: { position: { x: 1344, y: -624 }, size: { width: 96, height: 96 }, collapsed: false },
      eachAttachment: { position: { x: 1600, y: -720 }, size: { width: 560, height: 256 }, collapsed: false },
      attachToTicket: { position: { x: 336, y: 80 }, size: { width: 96, height: 96 }, collapsed: false },
      downloadAttachment1: { position: { x: 128, y: 80 }, size: { width: 96, height: 96 }, collapsed: false },
      notSpam: { position: { x: 704, y: -208 }, size: { width: 96, height: 96 }, collapsed: false },
      jiraSite: { position: { x: 1248, y: -272 }, size: { width: 96, height: 96 }, collapsed: false },
      postSlack: { position: { x: 1408, y: -272 }, size: { width: 96, height: 96 }, collapsed: false },
      draftReply: { position: { x: 1568, y: -272 }, size: { width: 96, height: 96 }, collapsed: false },
      markRead: { position: { x: 1776, y: -192 }, size: { width: 96, height: 96 }, collapsed: false },
      end: { position: { x: 2048, y: -192 }, size: { width: 96, height: 96 }, collapsed: false },
    },
    edges: {
      "byCategory->ticketSpam": { waypoints: [{ x: 928, y: -544, id: "wp-d0c4faf3-f92e-49f6-bc09-c19aa3a03d22" }, { x: 928, y: -496.0025702482876, id: "wp-fb72a8ae-c5f1-432c-b731-ab391ecd8a41" }] },
    },
  })
  .build();

function collectAttachment($vars: FlowVars) {
  const files = $vars.downloadedFiles || [];
  return { files: files.concat([$vars.downloadAttachment1.output]) };
}

function prepareFiles($vars: FlowVars) {
  const files = $vars.downloadedFiles || [];
  const readable = [];
  const other = [];
  for (const f of files) {
    const mime = String((f && f.MimeType) || "").toLowerCase();
    const name = String((f && f.FullName) || "").toLowerCase();
    const isPdf = mime === "application/pdf" || /\.pdf$/.test(name);
    const isImage = mime.indexOf("image/") === 0 || /\.(png|jpe?g|gif|webp|bmp|tiff?|heic)$/.test(name);
    if (isPdf || isImage) readable.push(f);
    else other.push(f);
  }
  const attachmentList = readable.length === 0 ? "(none)" : JSON.stringify(readable.map((f) => ({ ID: f.ID, FullName: f.FullName, MimeType: f.MimeType })), null, 2);
  const otherAttachments = other.length === 0 ? "(none)" : other.map((f) => f.FullName).join(", ");
  return { attachments: readable, attachmentList: attachmentList, otherAttachments: otherAttachments };
}
