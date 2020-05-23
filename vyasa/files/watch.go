package files

import (
	"log"
	"path/filepath"

	"github.com/fsnotify/fsnotify"
)

// Watch watches for files changes on paths and executes action if anything has changed
func Watch(paths []string, action func()) {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		log.Fatal(err)
	}
	defer watcher.Close()
	done := make(chan bool)

	go func() {
		for {
			select {
			case event, ok := <-watcher.Events:
				if !ok {
					return
				}
				if ext := filepath.Ext(event.Name); ext == ExtYAML {
					log.Printf("Applying %v changes", event.Name)
					action()
				}
			case err, ok := <-watcher.Errors:
				if !ok {
					return
				}
				log.Printf("files: %v", err)
			}
		}
	}()

	for _, path := range paths {
		err = watcher.Add(path)
		if err != nil {
			log.Fatal(err)
		}
	}

	<-done
}
