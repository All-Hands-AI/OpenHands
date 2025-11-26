#[test_only]
module vibe_balance::vibe_balance_tests {
    use std::signer;
    use lumio_framework::lumio_coin::{Self, LumioCoin};
    use lumio_framework::coin;
    use vibe_balance::vibe_balance;

    #[test(admin = @vibe_balance)]
    public fun test_initialize(admin: &signer) {
        vibe_balance::initialize(admin);

        let token_price = vibe_balance::get_token_price();
        assert!(token_price == 1, 0);
    }

    #[test(admin = @vibe_balance)]
    #[expected_failure(abort_code = 0x80002)]
    public fun test_initialize_twice(admin: &signer) {
        vibe_balance::initialize(admin);
        vibe_balance::initialize(admin);
    }

    #[test(admin = @vibe_balance, user = @0x123)]
    public fun test_whitelist_add(admin: &signer, user: address) {
        vibe_balance::initialize(admin);

        assert!(!vibe_balance::is_whitelisted(user), 1);

        vibe_balance::add_to_whitelist(admin, user);

        assert!(vibe_balance::is_whitelisted(user), 2);
    }

    #[test(admin = @vibe_balance, user = @0x123)]
    #[expected_failure(abort_code = 0x80007)]
    public fun test_whitelist_add_duplicate(admin: &signer, user: address) {
        vibe_balance::initialize(admin);

        vibe_balance::add_to_whitelist(admin, user);
        vibe_balance::add_to_whitelist(admin, user);
    }

    #[test(admin = @vibe_balance, user = @0x123)]
    public fun test_whitelist_remove(admin: &signer, user: address) {
        vibe_balance::initialize(admin);

        vibe_balance::add_to_whitelist(admin, user);
        assert!(vibe_balance::is_whitelisted(user), 1);

        vibe_balance::remove_from_whitelist(admin, user);
        assert!(!vibe_balance::is_whitelisted(user), 2);
    }

    #[test(admin = @vibe_balance, user1 = @0x123, user2 = @0x456, user3 = @0x789)]
    public fun test_batch_whitelist_add(
        admin: &signer,
        user1: address,
        user2: address,
        user3: address
    ) {
        vibe_balance::initialize(admin);

        let users = std::vector::empty<address>();
        std::vector::push_back(&mut users, user1);
        std::vector::push_back(&mut users, user2);
        std::vector::push_back(&mut users, user3);

        vibe_balance::batch_add_to_whitelist(admin, users);

        assert!(vibe_balance::is_whitelisted(user1), 1);
        assert!(vibe_balance::is_whitelisted(user2), 2);
        assert!(vibe_balance::is_whitelisted(user3), 3);
    }

    #[test(admin = @vibe_balance, user1 = @0x123, user2 = @0x456)]
    public fun test_batch_whitelist_remove(
        admin: &signer,
        user1: address,
        user2: address
    ) {
        vibe_balance::initialize(admin);

        vibe_balance::add_to_whitelist(admin, user1);
        vibe_balance::add_to_whitelist(admin, user2);

        let users = std::vector::empty<address>();
        std::vector::push_back(&mut users, user1);
        std::vector::push_back(&mut users, user2);

        vibe_balance::batch_remove_from_whitelist(admin, users);

        assert!(!vibe_balance::is_whitelisted(user1), 1);
        assert!(!vibe_balance::is_whitelisted(user2), 2);
    }

    #[test(admin = @vibe_balance, lumio_framework = @lumio_framework, user = @0x123)]
    public fun test_deposit(
        admin: &signer,
        lumio_framework: &signer,
        user: &signer
    ) {
        let user_addr = signer::address_of(user);

        vibe_balance::initialize(admin);
        vibe_balance::add_to_whitelist(admin, user_addr);

        let (burn_cap, mint_cap) = lumio_coin::initialize_for_test(lumio_framework);
        coin::register<LumioCoin>(user);

        let coins = coin::mint<LumioCoin>(1000, &mint_cap);
        coin::deposit(user_addr, coins);

        vibe_balance::deposit(user, 500);

        let balance = vibe_balance::get_balance(user_addr);
        assert!(balance == 500, 1);

        coin::destroy_burn_cap(burn_cap);
        coin::destroy_mint_cap(mint_cap);
    }

    #[test(admin = @vibe_balance, lumio_framework = @lumio_framework, user = @0x123)]
    #[expected_failure(abort_code = 0x50006)]
    public fun test_deposit_not_whitelisted(
        admin: &signer,
        lumio_framework: &signer,
        user: &signer
    ) {
        let user_addr = signer::address_of(user);

        vibe_balance::initialize(admin);

        let (burn_cap, mint_cap) = lumio_coin::initialize_for_test(lumio_framework);
        coin::register<LumioCoin>(user);

        let coins = coin::mint<LumioCoin>(1000, &mint_cap);
        coin::deposit(user_addr, coins);

        vibe_balance::deposit(user, 500);

        coin::destroy_burn_cap(burn_cap);
        coin::destroy_mint_cap(mint_cap);
    }

    #[test(admin = @vibe_balance)]
    public fun test_set_token_price(admin: &signer) {
        vibe_balance::initialize(admin);

        let initial_price = vibe_balance::get_token_price();
        assert!(initial_price == 1, 1);

        vibe_balance::set_token_price(admin, 10);

        let new_price = vibe_balance::get_token_price();
        assert!(new_price == 10, 2);
    }

    #[test(admin = @vibe_balance, lumio_framework = @lumio_framework, user = @0x123)]
    public fun test_batch_deduct(
        admin: &signer,
        lumio_framework: &signer,
        user: &signer
    ) {
        let user_addr = signer::address_of(user);

        vibe_balance::initialize(admin);
        vibe_balance::add_to_whitelist(admin, user_addr);

        let (burn_cap, mint_cap) = lumio_coin::initialize_for_test(lumio_framework);
        coin::register<LumioCoin>(user);

        let coins = coin::mint<LumioCoin>(1000, &mint_cap);
        coin::deposit(user_addr, coins);

        vibe_balance::deposit(user, 1000);

        let users = std::vector::empty<address>();
        std::vector::push_back(&mut users, user_addr);

        let tokens = std::vector::empty<u64>();
        std::vector::push_back(&mut tokens, 100);

        vibe_balance::batch_deduct(admin, users, tokens);

        let balance = vibe_balance::get_balance(user_addr);
        assert!(balance == 900, 1);

        coin::destroy_burn_cap(burn_cap);
        coin::destroy_mint_cap(mint_cap);
    }

    #[test(admin = @vibe_balance, lumio_framework = @lumio_framework, user = @0x123)]
    public fun test_batch_deduct_with_price(
        admin: &signer,
        lumio_framework: &signer,
        user: &signer
    ) {
        let user_addr = signer::address_of(user);

        vibe_balance::initialize(admin);
        vibe_balance::add_to_whitelist(admin, user_addr);
        vibe_balance::set_token_price(admin, 10);

        let (burn_cap, mint_cap) = lumio_coin::initialize_for_test(lumio_framework);
        coin::register<LumioCoin>(user);

        let coins = coin::mint<LumioCoin>(1000, &mint_cap);
        coin::deposit(user_addr, coins);

        vibe_balance::deposit(user, 1000);

        let users = std::vector::empty<address>();
        std::vector::push_back(&mut users, user_addr);

        let tokens = std::vector::empty<u64>();
        std::vector::push_back(&mut tokens, 10);

        vibe_balance::batch_deduct(admin, users, tokens);

        let balance = vibe_balance::get_balance(user_addr);
        assert!(balance == 900, 1);

        coin::destroy_burn_cap(burn_cap);
        coin::destroy_mint_cap(mint_cap);
    }

    #[test(admin = @vibe_balance, lumio_framework = @lumio_framework, user = @0x123)]
    #[expected_failure(abort_code = 0x30003)]
    public fun test_batch_deduct_insufficient_balance(
        admin: &signer,
        lumio_framework: &signer,
        user: &signer
    ) {
        let user_addr = signer::address_of(user);

        vibe_balance::initialize(admin);
        vibe_balance::add_to_whitelist(admin, user_addr);

        let (burn_cap, mint_cap) = lumio_coin::initialize_for_test(lumio_framework);
        coin::register<LumioCoin>(user);

        let coins = coin::mint<LumioCoin>(100, &mint_cap);
        coin::deposit(user_addr, coins);

        vibe_balance::deposit(user, 100);

        let users = std::vector::empty<address>();
        std::vector::push_back(&mut users, user_addr);

        let tokens = std::vector::empty<u64>();
        std::vector::push_back(&mut tokens, 200);

        vibe_balance::batch_deduct(admin, users, tokens);

        coin::destroy_burn_cap(burn_cap);
        coin::destroy_mint_cap(mint_cap);
    }

    #[test(admin = @vibe_balance, lumio_framework = @lumio_framework, user1 = @0x123, user2 = @0x456)]
    public fun test_batch_deduct_multiple_users(
        admin: &signer,
        lumio_framework: &signer,
        user1: &signer,
        user2: &signer
    ) {
        let user1_addr = signer::address_of(user1);
        let user2_addr = signer::address_of(user2);

        vibe_balance::initialize(admin);
        vibe_balance::add_to_whitelist(admin, user1_addr);
        vibe_balance::add_to_whitelist(admin, user2_addr);

        let (burn_cap, mint_cap) = lumio_coin::initialize_for_test(lumio_framework);
        coin::register<LumioCoin>(user1);
        coin::register<LumioCoin>(user2);

        let coins1 = coin::mint<LumioCoin>(1000, &mint_cap);
        coin::deposit(user1_addr, coins1);
        let coins2 = coin::mint<LumioCoin>(500, &mint_cap);
        coin::deposit(user2_addr, coins2);

        vibe_balance::deposit(user1, 1000);
        vibe_balance::deposit(user2, 500);

        let users = std::vector::empty<address>();
        std::vector::push_back(&mut users, user1_addr);
        std::vector::push_back(&mut users, user2_addr);

        let tokens = std::vector::empty<u64>();
        std::vector::push_back(&mut tokens, 100);
        std::vector::push_back(&mut tokens, 50);

        vibe_balance::batch_deduct(admin, users, tokens);

        let balance1 = vibe_balance::get_balance(user1_addr);
        let balance2 = vibe_balance::get_balance(user2_addr);

        assert!(balance1 == 900, 1);
        assert!(balance2 == 450, 2);

        coin::destroy_burn_cap(burn_cap);
        coin::destroy_mint_cap(mint_cap);
    }
}
