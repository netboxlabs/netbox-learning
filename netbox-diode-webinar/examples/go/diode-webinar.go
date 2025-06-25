package main

import (
	"context"
	"log"

	"github.com/netboxlabs/diode-sdk-go/diode"
)

func main() {
	client, err := diode.NewClient(
		"grpc://<diode.ip:diode.port>/diode",
		"example-app",
		"0.1.0",
		diode.WithClientID("YOUR_CLIENT_ID"),
		diode.WithClientSecret("YOUR_CLIENT_SECRET"),
	)
	if err != nil {
		log.Fatal(err)
	}

	// Create a device
	deviceEntity := &diode.Device{
		Name: diode.String("PDU 05"),
		DeviceType: &diode.DeviceType{
			Model: diode.String("AP7955"),
			Manufacturer: &diode.Manufacturer{
				Name: diode.String("APC"),
			},
		},
		Platform: &diode.Platform{
			Name: diode.String("APCOS"),
			Manufacturer: &diode.Manufacturer{
				Name: diode.String("APC"),
			},
		},
		Site: &diode.Site{
			Name: diode.String("Sunderland"),
		},
		Role: &diode.DeviceRole{
			Name: diode.String("Rack PDU"),
		},
		Status:   diode.String("active"),
	}

	entities := []diode.Entity{
		deviceEntity,
	}

	resp, err := client.Ingest(context.Background(), entities)
	if err != nil {
		log.Fatal(err)
	}
	if resp != nil && resp.Errors != nil {
		log.Printf("Errors: %v\n", resp.Errors)
	} else {
		log.Printf("Success\n")
	}

}
