use pinocchio::error::ProgramError;
use pinocchio::{AccountView, Address, ProgramResult};

use crate::state::{read_u64, Config};

/// Move `amount` lamports from the vault to `recipient`. Only the config's authority may do this.
pub fn process(program_id: &Address, accounts: &mut [AccountView], data: &[u8]) -> ProgramResult {
    let [config, vault, authority, recipient, ..] = accounts else {
        return Err(ProgramError::NotEnoughAccountKeys);
    };
    let amount = read_u64(data)?;
    if !authority.is_signer() {
        return Err(ProgramError::MissingRequiredSignature);
    }
    let cfg = Config::load(&config.try_borrow()?)?;
    if cfg.authority != *authority.address().as_array() {
        return Err(ProgramError::Custom(1));
    }
    if cfg.vault != *vault.address().as_array() || !vault.owned_by(program_id) {
        return Err(ProgramError::InvalidAccountData);
    }
    let remaining = vault.lamports().checked_sub(amount).ok_or(ProgramError::InsufficientFunds)?;
    let credited = recipient.lamports().checked_add(amount).ok_or(ProgramError::ArithmeticOverflow)?;
    vault.set_lamports(remaining);
    recipient.set_lamports(credited);
    Ok(())
}
