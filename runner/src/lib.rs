//! Helpers for case tests. A test file starts with `use case_runner::prelude::*;`.
//!
//! The harness sets PROGRAM_SO (path of the compiled program) and PROGRAM_ID
//! (its address, from the case's Cargo.toml) before running the tests.

use sha2::{Digest, Sha256};

pub mod prelude {
    pub use crate::{
        anchor_account_disc, anchor_ix, anchor_ix_disc, funded_keypair, program_account, program_id,
        send, setup,
    };
    pub use litesvm::LiteSVM;
    pub use solana_account::Account;
    pub use solana_address::Address;
    pub use solana_instruction::{AccountMeta, Instruction};
    pub use solana_keypair::Keypair;
    pub use solana_signer::Signer;
}

use prelude::*;

/// System program address.
pub const SYSTEM_PROGRAM: Address = Address::new_from_array([0u8; 32]);

/// Address of the program under test.
pub fn program_id() -> Address {
    std::env::var("PROGRAM_ID").expect("PROGRAM_ID not set").parse().expect("PROGRAM_ID is not an address")
}

/// A fresh VM with the program under test loaded at program_id().
pub fn setup() -> (LiteSVM, Address) {
    let id = program_id();
    let mut svm = LiteSVM::new();
    svm.add_program_from_file(id, std::env::var("PROGRAM_SO").expect("PROGRAM_SO not set"))
        .expect("load program");
    (svm, id)
}

/// A new keypair holding `lamports`.
pub fn funded_keypair(svm: &mut LiteSVM, lamports: u64) -> Keypair {
    let kp = Keypair::new();
    svm.airdrop(&kp.pubkey(), lamports).expect("airdrop");
    kp
}

/// An account owned by `owner` with the given data (rent-exempt for its size).
pub fn program_account(svm: &LiteSVM, owner: Address, data: Vec<u8>) -> Account {
    let lamports = svm.minimum_balance_for_rent_exemption(data.len());
    Account { lamports, data, owner, executable: false, rent_epoch: 0 }
}

/// Sign and send one transaction; `signers[0]` pays the fee.
/// Returns Err(log) when the transaction fails.
pub fn send(svm: &mut LiteSVM, ixs: &[Instruction], signers: &[&Keypair]) -> Result<(), String> {
    let payer = signers[0].pubkey();
    let msg = solana_message::Message::new(ixs, Some(&payer));
    let tx = solana_transaction::Transaction::new(signers, msg, svm.latest_blockhash());
    svm.send_transaction(tx).map(|_| ()).map_err(|e| format!("{:?}\n{}", e.err, e.meta.logs.join("\n")))
}

/// Anchor instruction discriminator: sha256("global:<name>")[..8].
pub fn anchor_ix_disc(name: &str) -> [u8; 8] {
    Sha256::digest(format!("global:{name}")).as_slice()[..8].try_into().unwrap()
}

/// Anchor account discriminator: sha256("account:<Type>")[..8].
pub fn anchor_account_disc(name: &str) -> [u8; 8] {
    Sha256::digest(format!("account:{name}")).as_slice()[..8].try_into().unwrap()
}

/// Anchor instruction data: discriminator followed by borsh-encoded args.
pub fn anchor_ix(name: &str, args: &[u8]) -> Vec<u8> {
    let mut data = anchor_ix_disc(name).to_vec();
    data.extend_from_slice(args);
    data
}
