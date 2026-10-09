-- Proofs fold under the result they prove.
--
--   ::: {.proof hint="add and subtract the conditional mean"}
--   ...
--   :::
--
-- becomes a fold titled "Proof" (or the div's title attribute) with the hint
-- beside it. components.lua renders it; the CSS attaches it to the box above.

local function md_blocks(s)
  if s == nil or s == "" then return pandoc.Blocks({}) end
  return pandoc.read(s, "markdown").blocks
end

local function part(name, blocks)
  return pandoc.Div(blocks, pandoc.Attr("", { "blog-part" }, { ["data-part"] = name }))
end

function Div(div)
  if not div.classes:includes("proof") then return nil end
  local title = div.attributes["title"] or "Proof"
  return pandoc.Div({
    part("title", md_blocks(title)),
    part("hint", md_blocks(div.attributes["hint"])),
    part("body", div.content),
  }, pandoc.Attr(div.identifier, { "blog-marker" }, {
    ["data-kind"] = "fold",
    ["data-role"] = "single",
    ["data-proof"] = "true",
  }))
end
