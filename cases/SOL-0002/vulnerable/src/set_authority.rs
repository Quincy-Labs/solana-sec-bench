use pinocchio::error::ProgramError;
use pinocchio::{AccountView, Address, ProgramResult};

use crate::state::Config;

/// Hand the vault over to a new authority. Only the current authority may do this.
pub fn process(program_id: &Address, accounts: &mut [AccountView], data: &[u8]) -> ProgramResult {
    let [config, authority, ..] = accounts else {
        return Err(ProgramError::NotEnoughAccountKeys);
    };
    let new_authority: [u8; 32] = data.get(..32).ok_or(ProgramError::InvalidInstructionData)?.try_into().unwrap();
    if !authority.is_signer() {
        return Err(ProgramError::MissingRequiredSignature);
    }
    if !config.owned_by(program_id) {
        return Err(ProgramError::IncorrectProgramId);
    }
    let mut bytes = config.try_borrow_mut()?;
    let cfg = Config::load(&bytes)?;
    if cfg.authority != *authority.address().as_array() {
        return Err(ProgramError::Custom(1));
    }
    bytes[8..40].copy_from_slice(&new_authority);
    Ok(())
}
