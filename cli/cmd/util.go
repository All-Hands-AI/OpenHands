package cmd

import (
	"fmt"
	"net"
	"net/http"
	"time"
)

func findFreePort() (int, error) {
	li, err := net.Listen("tcp", ":0")
	if err != nil {
		return 0, err
	}
	defer li.Close()

	addr := li.Addr().(*net.TCPAddr)
	return addr.Port, nil
}

func pollPage(url string, timeout time.Duration) (bool, error) {
	ch := time.After(timeout)

	ticker := time.NewTicker(3 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ch:
			return false, fmt.Errorf("timed out waiting for the page after %v", timeout)
		case <-ticker.C:
			resp, err := http.Get(url)
			if err != nil {
				continue
			}
			defer resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				return true, nil
			}
		}
	}
}

func splitBy(args []string, sep string) ([]string, []string) {
	idx := len(args)
	idx1 := idx

	for i, v := range args {
		if v == sep {
			idx = i
			idx1 = i + 1
			break
		}
	}

	return args[:idx], args[idx1:]
}
