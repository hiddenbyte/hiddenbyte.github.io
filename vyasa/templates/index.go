package templates

import (
	"html/template"
	"os"
	"sort"
)

// DefaultIndexTemplateStyle entry template default style
const DefaultIndexTemplateStyle = "/css/index.css"

// IndexTmplData index template data
type IndexTmplData struct {
	Entries chan EntryHTML
}

// IndexTmpl entry template
type IndexTmpl struct {
	t     *template.Template
	style string
}

// Execute execute entry template
func (tmpl IndexTmpl) Execute(tmplData *IndexTmplData, path string) (err error) {
	htmlDocument, err := os.Create(path)
	if err != nil {
		return
	}
	defer htmlDocument.Close()

	// Order entries by "created at"
	sortedEntries := make([]EntryHTML, 0)
	for entry := range tmplData.Entries {
		sortedEntries = append(sortedEntries, entry)
	}
	sort.Slice(sortedEntries, func(i, j int) bool { return sortedEntries[i].CreatedAt.After(sortedEntries[j].CreatedAt) })

	// Execute entry template
	err = tmpl.t.Execute(htmlDocument, struct {
		Entries []EntryHTML
		Style   string
	}{Entries: sortedEntries, Style: tmpl.style})

	if err != nil {
		return
	}

	return
}

// NewIndexTmpl creates an index template
func NewIndexTmpl(paths ...string) (IndexTmpl, error) {
	t, err := parseTemplate(paths)
	if err != nil {
		return IndexTmpl{}, err
	}
	return IndexTmpl{t, DefaultIndexTemplateStyle}, nil
}
