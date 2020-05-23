package main

import (
	"flag"
	"log"
	"os"
	"path/filepath"

	"github.com/hiddenbyte/vyasa/entries"
	"github.com/hiddenbyte/vyasa/files"
	"github.com/hiddenbyte/vyasa/server"

	"github.com/hiddenbyte/vyasa/templates"
)

var flagServer bool
var flagWatch bool
var flagCompile bool
var flagRootDir string

func init() {
	flag.BoolVar(&flagServer, "server", false, "start a fileserver")
	flag.BoolVar(&flagServer, "s", false, "start a fileserver (short)")

	flag.BoolVar(&flagWatch, "watch", false, "watch mode")
	flag.BoolVar(&flagWatch, "w", false, "watch mode (short)")

	flag.BoolVar(&flagCompile, "compile", false, "compile")
	flag.BoolVar(&flagCompile, "c", false, "compile (short)")

	flag.StringVar(&flagRootDir, "directory", ".", "root directory")
	flag.StringVar(&flagRootDir, "d", ".", "root directory (short)")
}

func main() {
	flag.Parse()
	switch {
	case flagCompile:
		compile(flagRootDir)
		if flagWatch {
			watch(flagRootDir)
		}
	case flagServer:
		if flagWatch {
			go startServer(flagRootDir)
			watch(flagRootDir)
		} else {
			startServer(flagRootDir)
		}
	case flagWatch:
		files.Watch([]string{"./entries/2020/05"}, func() { compile(flagRootDir) })
	default:
		flag.Usage()
		os.Exit(1)
	}
}

func compile(rootDir string) {
	entryHTMLDocuments := make(chan templates.EntryHTML)
	go createEntryHTMLDocuments(rootDir, entryHTMLDocuments)
	createIndexHTMLDocument(rootDir, templates.NewIndexTmplData(entryHTMLDocuments))
}

func startServer(rootDir string) {
	err := server.Start(rootDir, 8013)
	if err != nil {
		log.Fatal(err)
	}
}

func watch(rootDir string) {
	files.Watch([]string{"./entries/2020/05"}, func() { compile(rootDir) })
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
