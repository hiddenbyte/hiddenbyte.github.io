package server

import (
	"fmt"
	"net/http"
)

// Start starts a http file server
func Start(root string, port int) error {
	return http.ListenAndServe(fmt.Sprintf(":%v", port), http.FileServer(http.Dir(root)))
}
