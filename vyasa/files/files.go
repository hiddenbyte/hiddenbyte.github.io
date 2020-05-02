package files

import (
	"os"
	"path/filepath"
	"strings"
)

const (
	// ExtHTML html file extenstion
	ExtHTML = ".html"
	// ExtYAML yaml file extenstion
	ExtYAML = ".yaml"
)

// GetHTMLFileFor retrieves the provided file name with the extension replaced by ".html" - e.g. CreateHTMLFile("/x/y/someFile.data") returns "x/y/someFile.html".
func GetHTMLFileFor(name string) string {
	ext := filepath.Ext(name)

	var htmlPath string
	if ext != "" {
		htmlPath = strings.Replace(name, ext, ExtHTML, 1)
	} else {
		htmlPath = name + ExtHTML
	}

	return htmlPath
}

// GetFileNamesByExt retrieves all file paths inside the provided root path that matches with the specified extension.
func GetFileNamesByExt(root string, ext string, paths chan string) {
	filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && filepath.Ext(path) == ext {
			paths <- path
		}
		return nil
	})
	close(paths)
}
