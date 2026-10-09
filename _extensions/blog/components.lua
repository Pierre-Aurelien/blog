-- Builds the reading aids from the markers left by shortcodes.lua and
-- proofs.lua, adds the fold bar to posts that have folds, and loads the page
-- scripts. Runs after Quarto has rendered callouts, theorems, citations and
-- cross-references; maths is still Math, so MathJax renders it as usual.
--
-- Output classes match theme/components.scss:
--   .q          "The question" line          .take   takeaway
--   .bx.quiz    "Check yourself" box         .pcall  thinking principle
--   details.tog fold (details.tog.pf for a proof)    .foldbar  fold controls

local function is_marker(el)
  return el.classes ~= nil and el.classes:includes("blog-marker")
end

local function role(el) return el.attributes["data-role"] end
local function kind(el) return el.attributes["data-kind"] end

local function is_blank(il)
  return il.t == "Space" or il.t == "SoftBreak" or il.t == "LineBreak"
end

local function trim(inlines)
  while #inlines > 0 and is_blank(inlines[1]) do inlines:remove(1) end
  while #inlines > 0 and is_blank(inlines[#inlines]) do inlines:remove(#inlines) end
  return inlines
end

-- 1. Every marker becomes a block, and paired markers are joined. ----------

local function span_to_div(span)
  local parts = pandoc.Blocks({})
  for _, p in ipairs(span.content) do
    if p.t == "Span" and p.classes:includes("blog-part") then
      parts:insert(pandoc.Div({ pandoc.Plain(p.content) }, p.attr))
    end
  end
  return pandoc.Div(parts, span.attr)
end

-- A shortcode written on the line next to text lands inside a paragraph:
-- split the paragraph around it.
local function lift(blocks)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    local has = false
    if b.t == "Para" or b.t == "Plain" then
      for _, il in ipairs(b.content) do
        if il.t == "Span" and is_marker(il) then has = true break end
      end
    end
    if has then
      local cur = pandoc.Inlines({})
      local function flush()
        trim(cur)
        if #cur > 0 then out:insert(pandoc[b.t](cur)) end
        cur = pandoc.Inlines({})
      end
      for _, il in ipairs(b.content) do
        if il.t == "Span" and is_marker(il) then
          flush()
          out:insert(span_to_div(il))
        else
          cur:insert(il)
        end
      end
      flush()
    else
      out:insert(b)
    end
  end
  return out
end

local function body_part(blocks)
  return pandoc.Div(blocks, pandoc.Attr("", { "blog-part" }, { ["data-part"] = "body" }))
end

local function pair(blocks)
  local out = pandoc.Blocks({})
  local stack = {}
  local function target()
    return #stack > 0 and stack[#stack].content or out
  end
  for _, b in ipairs(blocks) do
    if b.t == "Div" and is_marker(b) and role(b) == "open" then
      table.insert(stack, { marker = b, content = pandoc.Blocks({}) })
    elseif b.t == "Div" and is_marker(b) and role(b) == "close" then
      local top = stack[#stack]
      if top ~= nil and kind(top.marker) == kind(b) then
        table.remove(stack)
        top.marker.attributes["data-role"] = "single"
        top.marker.content:insert(body_part(top.content))
        target():insert(top.marker)
      else
        quarto.log.warning("blog: {{< /" .. kind(b) .. " >}} has no matching {{< " .. kind(b) .. " >}}; ignored")
      end
    else
      target():insert(b)
    end
  end
  while #stack > 0 do
    local top = table.remove(stack)
    quarto.log.warning("blog: {{< " .. kind(top.marker) .. " >}} is never closed; its content is shown unwrapped")
    target():extend(top.content)
  end
  return out
end

-- 2. Markers become components. -------------------------------------------

local function parts_of(div)
  local p = {}
  for _, b in ipairs(div.content) do
    if b.t == "Div" and b.classes:includes("blog-part") then
      p[b.attributes["data-part"]] = b.content
    end
  end
  return p
end

local function inlines(blocks)
  if blocks == nil or #blocks == 0 then return pandoc.Inlines({}) end
  return pandoc.utils.blocks_to_inlines(blocks)
end

local function raw(s) return pandoc.RawInline("html", s) end
local function rawb(s) return pandoc.RawBlock("html", s) end
local function label(s) return pandoc.Span({ pandoc.Str(s) }, pandoc.Attr("", { "lab" })) end
local function attr(classes) return pandoc.Attr("", classes) end

local n_folds = 0

local function details(classes, id, title, hint, body)
  n_folds = n_folds + 1
  local summary = pandoc.Inlines({ raw('<summary><span class="tl">') })
  summary:extend(title)
  summary:insert(raw("</span>"))
  if #hint > 0 then
    summary:insert(raw('<span class="th">'))
    summary:extend(hint)
    summary:insert(raw("</span>"))
  end
  summary:insert(raw("</summary>"))
  local open = '<details class="' .. classes .. '"'
  if id ~= nil and id ~= "" then open = open .. ' id="' .. id .. '"' end
  local out = pandoc.Blocks({ rawb(open .. ">"), pandoc.Plain(summary), rawb('<div class="tb">') })
  out:extend(body or {})
  out:extend({ rawb("</div>"), rawb("</details>") })
  return out
end

-- Put a label at the start of the first paragraph, or on its own line.
local function with_label(lab, blocks)
  blocks = blocks or pandoc.Blocks({})
  local first = blocks[1]
  if first ~= nil and (first.t == "Para" or first.t == "Plain") then
    first.content:insert(1, lab)
    return blocks
  end
  blocks:insert(1, pandoc.Plain({ lab }))
  return blocks
end

local render = {
  question = function(p)
    local content = pandoc.Inlines({ label("The question") })
    content:extend(inlines(p.text))
    return pandoc.Div({ pandoc.Para(content) }, attr({ "q" }))
  end,

  takeaway = function(p, div)
    local lab = div.attributes["label"]
    if lab == nil or lab == "" then lab = "Takeaway" end
    local blocks = pandoc.Blocks({ pandoc.Plain({ label(lab) }) })
    blocks:extend(p.body or {})
    return pandoc.Div(blocks, attr({ "take" }))
  end,

  principle = function(p, div)
    local n = div.attributes["n"] or ""
    local blocks = pandoc.Blocks({
      pandoc.Plain({ pandoc.Span({ pandoc.Str(n) }, pandoc.Attr("", { "pn" }, { ["aria-hidden"] = "true" })) }),
      pandoc.Div(with_label(label("Thinking principle " .. n), p.body), attr({ "pt" })),
    })
    return pandoc.Div(blocks, attr({ "pcall" }))
  end,

  quiz = function(p)
    local blocks = pandoc.Blocks({ pandoc.Plain({ label("Check yourself") }) })
    blocks:extend(p.q or {})
    blocks:extend(details("tog", nil, { pandoc.Str("Answer") }, pandoc.Inlines({}), p.a))
    return pandoc.Div(blocks, attr({ "bx", "quiz" }))
  end,

  fold = function(p, div)
    local classes = div.attributes["data-proof"] == "true" and "tog pf" or "tog"
    return details(classes, div.identifier, inlines(p.title), inlines(p.hint), p.body)
  end,
}

local function render_marker(div)
  -- A callout's title attribute would also show as a tooltip over the box.
  if div.classes:includes("callout") and div.attributes["title"] ~= nil then
    div.attributes["title"] = nil
    return div
  end
  if not is_marker(div) or role(div) ~= "single" then return nil end
  local f = render[kind(div)]
  if f == nil then return nil end
  return f(parts_of(div), div)
end

-- 3. Fold bar and scripts. -------------------------------------------------

local function file_exists(path)
  local f = io.open(path, "r")
  if f ~= nil then f:close() return true end
  return false
end

local FOLDBAR = [[
<div class="foldbar"><span>Proofs, derivations, code and longer asides are folded so the main line stays short.</span><button type="button" data-fold="open">Unfold all</button><button type="button" data-fold="close">Fold all</button></div>
]]

-- The bar goes just before §1, after the scope box and key messages.
local function add_foldbar(doc)
  local at = 1
  for i, b in ipairs(doc.blocks) do
    local h = b
    if b.t == "Div" and b.classes:includes("section") then h = b.content[1] end
    if h ~= nil and h.t == "Header" and h.level == 2 then at = i break end
  end
  doc.blocks:insert(at, rawb(FOLDBAR))
  return doc
end

local function add_scripts()
  quarto.doc.add_html_dependency({
    name = "blog-components",
    version = "1.0.0",
    scripts = { "blog.js" },
  })
  -- A post with its own widgets.js gets the shared helpers first.
  local input = quarto.doc.input_file
  if input == nil then return end
  local dir = pandoc.path.directory(input)
  local own = pandoc.path.join({ dir, "widgets.js" })
  if file_exists(own) then
    quarto.doc.add_html_dependency({
      name = "blog-widgets",
      version = "1.0.0",
      scripts = { "../../shared/widgets.js" },
    })
    quarto.doc.add_html_dependency({
      name = "post-" .. pandoc.path.filename(dir),
      version = "1.0.0",
      scripts = { own },
    })
  end
end

if not quarto.doc.is_format("html") then
  return {}
end

return {
  { Blocks = function(blocks) return pair(lift(blocks)) end },
  { Div = render_marker },
  {
    Pandoc = function(doc)
      add_scripts()
      if n_folds > 0 then return add_foldbar(doc) end
      return nil
    end,
  },
}
