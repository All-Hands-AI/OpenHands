module vibe_balance::vibe_balance {
    use std::signer;
    use std::error;
    use lumio_framework::coin::{Self, Coin};
    use lumio_framework::lumio_coin::LumioCoin;
    use lumio_framework::event;
    use lumio_std::table::{Self, Table};

    const E_NOT_INITIALIZED: u64 = 1;
    const E_ALREADY_INITIALIZED: u64 = 2;
    const E_INSUFFICIENT_BALANCE: u64 = 3;
    const E_NOT_ADMIN: u64 = 4;
    const E_ARRAYS_LENGTH_MISMATCH: u64 = 5;
    const E_NOT_WHITELISTED: u64 = 6;
    const E_ALREADY_WHITELISTED: u64 = 7;
    const E_NOT_IN_WHITELIST: u64 = 8;

    struct BalanceStore has key {
        balances: Table<address, u64>,
        whitelist: Table<address, bool>,
        token_price_in_coins: u64,
        treasury: Coin<LumioCoin>,
    }

    #[event]
    struct DepositEvent has drop, store {
        user: address,
        amount: u64,
        new_balance: u64,
    }

    #[event]
    struct TokensDeductedEvent has drop, store {
        user: address,
        tokens_deducted: u64,
        coins_deducted: u64,
        new_balance: u64,
    }

    #[event]
    struct TokenPriceUpdatedEvent has drop, store {
        old_price: u64,
        new_price: u64,
    }

    #[event]
    struct BatchDeductionCompletedEvent has drop, store {
        total_users: u64,
        total_tokens_deducted: u64,
        total_coins_deducted: u64,
    }

    #[event]
    struct WhitelistAddedEvent has drop, store {
        user: address,
    }

    #[event]
    struct WhitelistRemovedEvent has drop, store {
        user: address,
    }

    #[event]
    struct BatchWhitelistEvent has drop, store {
        total_users: u64,
        added: bool,
    }

    public entry fun initialize(admin: &signer) {
        let admin_addr = signer::address_of(admin);

        assert!(!exists<BalanceStore>(admin_addr), error::already_exists(E_ALREADY_INITIALIZED));

        let balance_store = BalanceStore {
            balances: table::new(),
            whitelist: table::new(),
            token_price_in_coins: 1,
            treasury: coin::zero<LumioCoin>(),
        };

        move_to(admin, balance_store);
    }

    public entry fun add_to_whitelist(admin: &signer, user: address) acquires BalanceStore {
        let admin_addr = signer::address_of(admin);

        assert!(exists<BalanceStore>(admin_addr), error::not_found(E_NOT_INITIALIZED));

        let balance_store = borrow_global_mut<BalanceStore>(admin_addr);

        assert!(
            !table::contains(&balance_store.whitelist, user),
            error::already_exists(E_ALREADY_WHITELISTED)
        );

        table::add(&mut balance_store.whitelist, user, true);

        event::emit(WhitelistAddedEvent {
            user,
        });
    }

    public entry fun remove_from_whitelist(admin: &signer, user: address) acquires BalanceStore {
        let admin_addr = signer::address_of(admin);

        assert!(exists<BalanceStore>(admin_addr), error::not_found(E_NOT_INITIALIZED));

        let balance_store = borrow_global_mut<BalanceStore>(admin_addr);

        assert!(
            table::contains(&balance_store.whitelist, user),
            error::not_found(E_NOT_IN_WHITELIST)
        );

        table::remove(&mut balance_store.whitelist, user);

        event::emit(WhitelistRemovedEvent {
            user,
        });
    }

    public entry fun batch_add_to_whitelist(admin: &signer, users: vector<address>) acquires BalanceStore {
        let admin_addr = signer::address_of(admin);

        assert!(exists<BalanceStore>(admin_addr), error::not_found(E_NOT_INITIALIZED));

        let balance_store = borrow_global_mut<BalanceStore>(admin_addr);
        let total_users = std::vector::length(&users);

        let i = 0;
        while (i < total_users) {
            let user = *std::vector::borrow(&users, i);

            if (!table::contains(&balance_store.whitelist, user)) {
                table::add(&mut balance_store.whitelist, user, true);

                event::emit(WhitelistAddedEvent {
                    user,
                });
            };

            i = i + 1;
        };

        event::emit(BatchWhitelistEvent {
            total_users,
            added: true,
        });
    }

    public entry fun batch_remove_from_whitelist(admin: &signer, users: vector<address>) acquires BalanceStore {
        let admin_addr = signer::address_of(admin);

        assert!(exists<BalanceStore>(admin_addr), error::not_found(E_NOT_INITIALIZED));

        let balance_store = borrow_global_mut<BalanceStore>(admin_addr);
        let total_users = std::vector::length(&users);

        let i = 0;
        while (i < total_users) {
            let user = *std::vector::borrow(&users, i);

            if (table::contains(&balance_store.whitelist, user)) {
                table::remove(&mut balance_store.whitelist, user);

                event::emit(WhitelistRemovedEvent {
                    user,
                });
            };

            i = i + 1;
        };

        event::emit(BatchWhitelistEvent {
            total_users,
            added: false,
        });
    }

    public entry fun deposit(user: &signer, amount: u64) acquires BalanceStore {
        let user_addr = signer::address_of(user);
        let admin_addr = @vibe_balance;

        assert!(exists<BalanceStore>(admin_addr), error::not_found(E_NOT_INITIALIZED));

        let balance_store = borrow_global_mut<BalanceStore>(admin_addr);

        assert!(
            table::contains(&balance_store.whitelist, user_addr),
            error::permission_denied(E_NOT_WHITELISTED)
        );

        let coins = coin::withdraw<LumioCoin>(user, amount);

        coin::merge(&mut balance_store.treasury, coins);

        let current_balance = if (table::contains(&balance_store.balances, user_addr)) {
            *table::borrow(&balance_store.balances, user_addr)
        } else {
            0
        };

        let new_balance = current_balance + amount;

        if (table::contains(&balance_store.balances, user_addr)) {
            *table::borrow_mut(&mut balance_store.balances, user_addr) = new_balance;
        } else {
            table::add(&mut balance_store.balances, user_addr, new_balance);
        };

        event::emit(DepositEvent {
            user: user_addr,
            amount,
            new_balance,
        });
    }

    public entry fun set_token_price(admin: &signer, price_in_coins: u64) acquires BalanceStore {
        let admin_addr = signer::address_of(admin);

        assert!(exists<BalanceStore>(admin_addr), error::not_found(E_NOT_INITIALIZED));

        let balance_store = borrow_global_mut<BalanceStore>(admin_addr);

        let old_price = balance_store.token_price_in_coins;
        balance_store.token_price_in_coins = price_in_coins;

        event::emit(TokenPriceUpdatedEvent {
            old_price,
            new_price: price_in_coins,
        });
    }

    public entry fun batch_deduct(
        admin: &signer,
        users: vector<address>,
        tokens_amounts: vector<u64>
    ) acquires BalanceStore {
        let admin_addr = signer::address_of(admin);

        assert!(exists<BalanceStore>(admin_addr), error::not_found(E_NOT_INITIALIZED));
        assert!(
            std::vector::length(&users) == std::vector::length(&tokens_amounts),
            error::invalid_argument(E_ARRAYS_LENGTH_MISMATCH)
        );

        let balance_store = borrow_global_mut<BalanceStore>(admin_addr);
        let token_price = balance_store.token_price_in_coins;

        let total_users = std::vector::length(&users);
        let total_tokens_deducted = 0u64;
        let total_coins_deducted = 0u64;

        let i = 0;
        while (i < total_users) {
            let user_addr = *std::vector::borrow(&users, i);
            let tokens_to_deduct = *std::vector::borrow(&tokens_amounts, i);

            let coins_to_deduct = tokens_to_deduct * token_price;

            assert!(
                table::contains(&balance_store.balances, user_addr),
                error::not_found(E_INSUFFICIENT_BALANCE)
            );

            let current_balance = *table::borrow(&balance_store.balances, user_addr);

            assert!(
                current_balance >= coins_to_deduct,
                error::invalid_state(E_INSUFFICIENT_BALANCE)
            );

            let new_balance = current_balance - coins_to_deduct;
            *table::borrow_mut(&mut balance_store.balances, user_addr) = new_balance;

            total_tokens_deducted = total_tokens_deducted + tokens_to_deduct;
            total_coins_deducted = total_coins_deducted + coins_to_deduct;

            event::emit(TokensDeductedEvent {
                user: user_addr,
                tokens_deducted: tokens_to_deduct,
                coins_deducted: coins_to_deduct,
                new_balance,
            });

            i = i + 1;
        };

        event::emit(BatchDeductionCompletedEvent {
            total_users,
            total_tokens_deducted,
            total_coins_deducted,
        });
    }

    #[view]
    public fun get_balance(user_addr: address): u64 acquires BalanceStore {
        let admin_addr = @vibe_balance;

        if (!exists<BalanceStore>(admin_addr)) {
            return 0
        };

        let balance_store = borrow_global<BalanceStore>(admin_addr);

        if (!table::contains(&balance_store.balances, user_addr)) {
            return 0
        };

        *table::borrow(&balance_store.balances, user_addr)
    }

    #[view]
    public fun get_token_price(): u64 acquires BalanceStore {
        let admin_addr = @vibe_balance;

        if (!exists<BalanceStore>(admin_addr)) {
            return 1
        };

        let balance_store = borrow_global<BalanceStore>(admin_addr);
        balance_store.token_price_in_coins
    }

    #[view]
    public fun is_whitelisted(user_addr: address): bool acquires BalanceStore {
        let admin_addr = @vibe_balance;

        if (!exists<BalanceStore>(admin_addr)) {
            return false
        };

        let balance_store = borrow_global<BalanceStore>(admin_addr);

        table::contains(&balance_store.whitelist, user_addr)
    }
}
