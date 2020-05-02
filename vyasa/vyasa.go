package main

import (
	"log"
	"os"
	"path/filepath"

	"github.com/hiddenbyte/vyasa/entries"
	"github.com/hiddenbyte/vyasa/files"

	"github.com/hiddenbyte/vyasa/templates"
)

func main() {
	args := os.Args[1:]

	if len(args) != 2 {
		log.Fatal("no command was specified")
	}

	command := args[0]
	rootPath := args[1]

	if command != "compile" {
		log.Fatalf("unknown command '%s'", args[1])
	}

	entryHTMLDocuments := make(chan templates.EntryHTML)
	go createEntryHTMLDocuments(rootPath, entryHTMLDocuments)

	createIndexHTMLDocument(rootPath, &templates.IndexTmplData{Entries: entryHTMLDocuments})
}

// createEntryHTMLDocuments creates entry HTML documents
func createEntryHTMLDocuments(rootPath string, entryHTMLDocuments chan templates.EntryHTML) {
	// Create entry template
	indexTemplatePath := filepath.Join(rootPath, files.PathMasterTemplate)
	entriesTemplatePath := filepath.Join(rootPath, files.PathEntriesTemplate)
	entryTemplate, err := templates.CreateEntryTmpl(indexTemplatePath, entriesTemplatePath)
	if err != nil {
		log.Fatal(err)
		return
	}

	// Find all entry data
	entriesData := make(chan entries.Entry)
	entriesRootPath := filepath.Join(rootPath, files.PathEntriesRoot)
	go entries.Open(entriesRootPath, entriesData)

	// Create a HTML document for each entry
	for entry := range entriesData {
		tmplData, err := templates.NewEntryTmplData(entry.Title, entry.Content, entry.Time)
		if err != nil {
			log.Fatal(err)
			return
		}

		htmlDocument, err := entryTemplate.Execute(tmplData, files.GetHTMLFileFor(entry.Path))
		if err != nil {
			log.Fatal(err)
		}
		entryHTMLDocuments <- htmlDocument
	}
	close(entryHTMLDocuments)
}

// createIndexHTMLDocument creates index HTML document
func createIndexHTMLDocument(rootPath string, tmplData *templates.IndexTmplData) {
	// Create index template
	masterTemplatePath := filepath.Join(rootPath, files.PathMasterTemplate)
	indexTemplatePath := filepath.Join(rootPath, files.PathIndexTemplate)
	indexTemplate, err := templates.NewIndexTmpl(masterTemplatePath, indexTemplatePath)
	if err != nil {
		log.Fatal(err)
		return
	}

	err = indexTemplate.Execute(tmplData, files.PathIndexHTML)
	if err != nil {
		log.Fatal(err)
	}
}
