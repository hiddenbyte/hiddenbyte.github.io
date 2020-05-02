package entries

import (
	"log"
	"os"

	"github.com/hiddenbyte/vyasa/files"
	"gopkg.in/yaml.v2"
)

// Entry a blog entry
type Entry struct {
	Title   string `yaml:"Title"`
	Time    string `yaml:"Time"`
	Content string `yaml:"Content"`
	Path    string
}

// Open reads and retrieves all entries from rootPath
func Open(rootPath string, entries chan Entry) {
	entryFiles := make(chan string)
	go files.GetFileNamesByExt(rootPath, files.ExtYAML, entryFiles)

	for entryFile := range entryFiles {
		entry, err := parseFile(entryFile)
		if err != nil {
			log.Fatal(err)
		}
		entries <- entry
	}
	close(entries)
}

// parseFile parses the file as a blog entry
func parseFile(path string) (entry Entry, err error) {
	file, err := os.Open(path)
	defer file.Close()

	if err == nil {
		err = yaml.NewDecoder(file).Decode(&entry)
	}

	entry.Path = path
	return
}
