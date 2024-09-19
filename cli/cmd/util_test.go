package cmd

import (
	"reflect"
	"testing"
	"time"
)

func TestFindFreePort(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping test...")
	}
	_, err := findFreePort()
	if err != nil {
		t.Fatal(err)
	}
}

func TestPollPage(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping test...")
	}
	_, err := pollPage("https://docs.all-hands.dev/", 15*time.Second)
	if err != nil {
		t.Fatal(err)
	}
}

func TestSplitBy(t *testing.T) {
	tests := []struct {
		args  []string
		sep   string
		want1 []string
		want2 []string
	}{
		{[]string{"a", "b", "c"}, "--", []string{"a", "b", "c"}, []string{}},
		{[]string{"a", "b", "c", "--"}, "--", []string{"a", "b", "c"}, []string{}},
		{[]string{"a", "b", "--", "c"}, "--", []string{"a", "b"}, []string{"c"}},
		{[]string{"a", "--", "b", "c"}, "--", []string{"a"}, []string{"b", "c"}},
		{[]string{"--", "a", "b", "c"}, "--", []string{}, []string{"a", "b", "c"}},
		{[]string{}, "--", []string{}, []string{}},
	}

	for _, tt := range tests {
		got1, got2 := splitBy(tt.args, tt.sep)
		if !reflect.DeepEqual(got1, tt.want1) || !reflect.DeepEqual(got2, tt.want2) {
			t.Errorf("%v %s got (%v, %v), want (%v, %v)", tt.args, tt.sep, got1, got2, tt.want1, tt.want2)
		}
	}
}
