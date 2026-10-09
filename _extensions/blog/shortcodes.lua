-- Shortcodes for the reading aids: question, takeaway, quiz, principle, fold.
--
-- A Quarto shortcode cannot wrap content, so the paired ones
-- ({{< takeaway >}} ... {{< /takeaway >}}) emit an "open" and a "close"
-- marker, and components.lua gathers everything between them into one
-- component. Arguments are parsed as Markdown here, before Quarto resolves
-- maths, citations and cross-references, so all three work inside them.

local function text(v)
  if v == nil then return "" end
  if type(v) == "string" then return v end
  return pandoc.utils.stringify(v)
end

-- An argument is one line of inline Markdown. Escape what would otherwise
-- start a block: "64. By ..." is an answer, not an ordered list.
local function md_blocks(s)
  s = text(s)
  if s == "" then return pandoc.Blocks({}) end
  s = s:gsub("^(%s*%d+)([.)])", "%1\\%2")
  s = s:gsub("^(%s*)([-+*#>|])", "%1\\%2")
  return pandoc.read(s, "markdown").blocks
end

-- A marker is a Div in block position and a Span inside a paragraph.
-- Its parts (question text, quiz answer, fold title...) are children
-- tagged with data-part.
local function marker(kind, role, context, parts, attrs)
  local attr = pandoc.Attr("", { "blog-marker" }, attrs or {})
  attr.attributes["data-kind"] = kind
  attr.attributes["data-role"] = role
  local children = {}
  for _, p in ipairs(parts or {}) do
    local pattr = pandoc.Attr("", { "blog-part" }, { ["data-part"] = p[1] })
    if context == "block" then
      table.insert(children, pandoc.Div(p[2], pattr))
    else
      table.insert(children, pandoc.Span(pandoc.utils.blocks_to_inlines(p[2]), pattr))
    end
  end
  if context == "block" then
    return pandoc.Div(children, attr)
  end
  return pandoc.Span(children, attr)
end

local function closer(kind)
  return function(_, _, _, _, context)
    return marker(kind, "close", context)
  end
end

return {
  -- {{< question "With no labels, what do we train an encoder against?" >}}
  ["question"] = function(args, kwargs, _, _, context)
    local q = args[1] or kwargs["q"]
    return marker("question", "single", context, { { "text", md_blocks(q) } })
  end,

  -- {{< takeaway >}} ... {{< /takeaway >}}
  ["takeaway"] = function(_, kwargs, _, _, context)
    return marker("takeaway", "open", context, {}, { label = text(kwargs["label"]) })
  end,
  ["/takeaway"] = closer("takeaway"),

  -- {{< quiz q="..." a="..." >}}
  ["quiz"] = function(_, kwargs, _, _, context)
    return marker("quiz", "single", context, {
      { "q", md_blocks(kwargs["q"]) },
      { "a", md_blocks(kwargs["a"]) },
    })
  end,

  -- {{< principle n="3" >}} ... {{< /principle >}}
  ["principle"] = function(_, kwargs, _, _, context)
    return marker("principle", "open", context, {}, { n = text(kwargs["n"]) })
  end,
  ["/principle"] = closer("principle"),

  -- {{< fold title="..." hint="..." >}} ... {{< /fold >}}
  ["fold"] = function(_, kwargs, _, _, context)
    return marker("fold", "open", context, {
      { "title", md_blocks(kwargs["title"]) },
      { "hint", md_blocks(kwargs["hint"]) },
    })
  end,
  ["/fold"] = closer("fold"),
}
