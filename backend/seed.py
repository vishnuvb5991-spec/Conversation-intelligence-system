from .schemas import Document


SEED_DOCUMENTS = [
    Document(id="slack-launch", source="Slack", title="#launch-room · Go-to-market check-in", author="Maya Chen", text="The Enterprise plan is approved for a phased launch. Sales enablement needs final competitive positioning and an updated security one-pager before the November 4 announcement.", url="slack://launch-room/2026-10-24"),
    Document(id="confluence-launch", source="Confluence", title="Enterprise launch plan", author="Growth team", text="Phase one starts with existing design partners. The public release is targeted for November 4, contingent on legal approval of updated terms and the security review.", url="https://confluence.example/enterprise-launch"),
    Document(id="jira-gtm", source="Jira", title="GTM-184 · Finalize launch enablement", author="Alex Morgan", text="Complete the battlecard, announcement brief, and account list. Dependencies LEGAL-72 and SEC-91 must be resolved before external communications are scheduled.", url="https://jira.example/browse/GTM-184"),
    Document(id="email-announcement", source="Email", title="Re: Enterprise announcement timing", author="Priya Shah", text="We can support a November 4 launch provided customer-facing documents use the approved claims. Final legal language will be shared by Friday.", url="mailto:priya@example.com"),
    Document(id="drive-narrative", source="Drive", title="Enterprise launch narrative v3", author="Marketing", text="The core story centers on trusted knowledge access with source-grounded answers, permission-aware retrieval, and measurable time to insight.", url="https://drive.example/enterprise-narrative"),
]
