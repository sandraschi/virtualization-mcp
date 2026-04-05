# Gemini Repo Rules (virtualization-mcp)

## Implementation Honesty

- Early prototype placeholders are allowed only when clearly temporary.
- Pre-release/production code must not fake success.
- If provider/model/integration is unavailable, return explicit `not_implemented` errors.
- Do not emit synthetic findings/metrics as if they are real.
- Webapp features that are not implemented must visibly show **Under construction**.

## Anti-gaslight contract

- Never claim success for unimplemented operations.
- Never hide unavailable behavior behind silent no-op.
- Include actionable recovery guidance in failure responses.

## References

- `D:/Dev/repos/mcp-central-docs/standards/IMPLEMENTATION_HONESTY_STANDARD.md`
- `D:/Dev/repos/mcp-central-docs/standards/TOOL_DESIGN_STANDARDS.md`
