package templates

import "html/template"

func parseTemplate(paths []string) (t *template.Template, err error) {
	t, err = template.ParseFiles(paths...)
	return
}
