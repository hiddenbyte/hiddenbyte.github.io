package templates

import (
	"html/template"
	"os"
)

// IndexTmplData index template data
type IndexTmplData struct {
	Entries chan EntryHTML
}

// IndexTmpl entry template
type IndexTmpl struct {
	t *template.Template
}

// Execute execute entry template
func (tmpl IndexTmpl) Execute(entry *IndexTmplData, path string) (err error) {
	htmlDocument, err := os.Create(path)
	if err != nil {
		return
	}
	defer htmlDocument.Close()

	// Execute entry template
	err = tmpl.t.Execute(htmlDocument, entry)
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
	return IndexTmpl{t}, nil
}
