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
	Entries []EntryHTML
}

// NewIndexTmplData creates a new index template data
func NewIndexTmplData(entries chan EntryHTML) *IndexTmplData {
	sortedEntries := make([]EntryHTML, 0)
	for entry := range entries {
		sortedEntries = append(sortedEntries, entry)
	}
	sort.Slice(sortedEntries, func(i, j int) bool { return sortedEntries[i].CreatedAt.After(sortedEntries[j].CreatedAt) })
	return &IndexTmplData{sortedEntries}
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

	// Execute entry template
	err = tmpl.t.Execute(htmlDocument, struct {
		*MasterTmplData
		*IndexTmplData
	}{MasterTmplData: &MasterTmplData{Style: tmpl.style}, IndexTmplData: tmplData})

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
