LUMIO_BIN ?= /Users/dimaakusev/Documents/projects/lumio/lumio-node/target/debug/lumio
CONTRACT ?= 0xac1f48e2c77b95f2646c37ff629dbd27fa1a1f0857f7260ddf59ed14a13063fb

.PHONY: build test deploy-testnet deploy-mainnet init-testnet init-mainnet \
        deposit balance whitelist-add whitelist-remove whitelist-check \
        deduct set-price get-price

# Build & Test
build:
	$(LUMIO_BIN) move compile --named-addresses vibe_balance=$$($(LUMIO_BIN) account lookup-address | grep -oE '0x[a-fA-F0-9]+' | head -1)

test:
	$(LUMIO_BIN) move test --named-addresses vibe_balance=$$($(LUMIO_BIN) account lookup-address | grep -oE '0x[a-fA-F0-9]+' | head -1)

# Deploy
deploy-testnet:
	LUMIO_NETWORK=testnet ./scripts/deploy.sh

deploy-mainnet:
	LUMIO_NETWORK=mainnet ./scripts/deploy.sh

init-testnet:
	LUMIO_NETWORK=testnet ./scripts/deploy.sh --init

init-mainnet:
	LUMIO_NETWORK=mainnet ./scripts/deploy.sh --init

# Deposit (amount in micro-coins, e.g., 1000000 = 1 coin)
# Usage: make deposit AMOUNT=1000000
deposit:
	@if [ -z "$(AMOUNT)" ]; then echo "Usage: make deposit AMOUNT=<amount>"; exit 1; fi
	$(LUMIO_BIN) move run --function-id "$(CONTRACT)::vibe_balance::deposit" --args "u64:$(AMOUNT)" --assume-yes

# Check balance
# Usage: make balance ADDRESS=0x...
balance:
	@if [ -z "$(ADDRESS)" ]; then echo "Usage: make balance ADDRESS=<address>"; exit 1; fi
	@curl -s -X POST "https://api.testnet.lumio.io/v1/view" \
		-H "Content-Type: application/json" \
		-d '{"function":"$(CONTRACT)::vibe_balance::get_balance","type_arguments":[],"arguments":["$(ADDRESS)"]}' \
		| jq -r '.[0]'

# Whitelist management
# Usage: make whitelist-add ADDRESS=0x...
whitelist-add:
	@if [ -z "$(ADDRESS)" ]; then echo "Usage: make whitelist-add ADDRESS=<address>"; exit 1; fi
	$(LUMIO_BIN) move run --function-id "$(CONTRACT)::vibe_balance::add_to_whitelist" --args "address:$(ADDRESS)" --assume-yes

# Usage: make whitelist-remove ADDRESS=0x...
whitelist-remove:
	@if [ -z "$(ADDRESS)" ]; then echo "Usage: make whitelist-remove ADDRESS=<address>"; exit 1; fi
	$(LUMIO_BIN) move run --function-id "$(CONTRACT)::vibe_balance::remove_from_whitelist" --args "address:$(ADDRESS)" --assume-yes

# Usage: make whitelist-check ADDRESS=0x...
whitelist-check:
	@if [ -z "$(ADDRESS)" ]; then echo "Usage: make whitelist-check ADDRESS=<address>"; exit 1; fi
	@curl -s -X POST "https://api.testnet.lumio.io/v1/view" \
		-H "Content-Type: application/json" \
		-d '{"function":"$(CONTRACT)::vibe_balance::is_whitelisted","type_arguments":[],"arguments":["$(ADDRESS)"]}' \
		| jq -r '.[0]'

# Deduct tokens (admin only)
# Usage: make deduct ADDRESS=0x... TOKENS=100
deduct:
	@if [ -z "$(ADDRESS)" ] || [ -z "$(TOKENS)" ]; then echo "Usage: make deduct ADDRESS=<address> TOKENS=<amount>"; exit 1; fi
	$(LUMIO_BIN) move run --function-id "$(CONTRACT)::vibe_balance::batch_deduct" \
		--args "address:[$(ADDRESS)]" "u64:[$(TOKENS)]" --assume-yes

# Token price management
# Usage: make set-price PRICE=2
set-price:
	@if [ -z "$(PRICE)" ]; then echo "Usage: make set-price PRICE=<price>"; exit 1; fi
	$(LUMIO_BIN) move run --function-id "$(CONTRACT)::vibe_balance::set_token_price" --args "u64:$(PRICE)" --assume-yes

get-price:
	@curl -s -X POST "https://api.testnet.lumio.io/v1/view" \
		-H "Content-Type: application/json" \
		-d '{"function":"$(CONTRACT)::vibe_balance::get_token_price","type_arguments":[],"arguments":[]}' \
		| jq -r '.[0]'

# Test wrapper
test-wrapper:
	npx tsx scripts/test-wrapper.ts
