package templates

import (
	"html/template"
	"os"
	"time"
)

// DefaultEntryTemplateStyle entry template default style
const DefaultEntryTemplateStyle = "/css/entry.css"

// EntryTmplData entry template data
type EntryTmplData struct {
	Title     string
	Content   template.HTML
	CreatedAt time.Time
}

// NewEntryTmplData creates a new instace of EntryTmplData
func NewEntryTmplData(title string, content string, createdAt string) (*EntryTmplData, error) {
	parsedCreateAt, err := time.Parse(time.RFC3339, createdAt)
	if err != nil {
		return nil, err
	}
	return &EntryTmplData{Title: title, Content: template.HTML(content), CreatedAt: parsedCreateAt}, nil
}

// EntryHTML entry template resulting html file
type EntryHTML struct {
	*EntryTmplData
	Path string
}

// EntryTmpl entry template
type EntryTmpl struct {
	t     *template.Template
	style string
}

// Execute execute entry template
func (tmpl EntryTmpl) Execute(entry *EntryTmplData, path string) (html EntryHTML, err error) {
	htmlDocument, err := os.Create(path)
	if err != nil {
		return
	}
	defer htmlDocument.Close()

	// Execute entry template
	err = tmpl.t.Execute(htmlDocument, struct {
		*MasterTmplData
		*EntryTmplData
	}{MasterTmplData: &MasterTmplData{Style: tmpl.style, DocumentTitle: entry.Title}, EntryTmplData: entry})

	if err != nil {
		return
	}

	html = EntryHTML{EntryTmplData: entry, Path: htmlDocument.Name()}
	return
}

// CreateEntryTmpl creates an entry template
func CreateEntryTmpl(paths ...string) (EntryTmpl, error) {
	t, err := parseTemplate(paths)
	if err != nil {
		return EntryTmpl{}, err
	}
	return EntryTmpl{t, DefaultEntryTemplateStyle}, nil
}
