//! Test fixture: instruction data is a u64 that is stored in the first account.
#![no_std]
use pinocchio::error::ProgramError;
use pinocchio::{entrypoint, nostd_panic_handler, AccountView, Address, ProgramResult};

entrypoint!(process_instruction);
nostd_panic_handler!();

pub fn process_instruction(_id: &Address, accounts: &mut [AccountView], data: &[u8]) -> ProgramResult {
    let [state, ..] = accounts else { return Err(ProgramError::NotEnoughAccountKeys) };
    let value = u64::from_le_bytes(data.get(..8).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap());
    let stored = value;
    state.try_borrow_mut()?[..8].copy_from_slice(&stored.to_le_bytes());
    Ok(())
}
