//! Treasury: holds a DAO's SOL and pays out grants. The treasury's authority
//! approves each payment and can hand the treasury over to a new authority.
use anchor_lang::prelude::*;

declare_id!("AxzFuxi43PnAGeVzejg4azcWJWf2ipvcaUCMRK485cMu");

#[program]
pub mod treasury {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let treasury = &mut ctx.accounts.treasury;
        treasury.authority = ctx.accounts.authority.key();
        treasury.total_paid = 0;
        Ok(())
    }

    /// Pay `amount` lamports of the treasury's SOL to `recipient`.
    pub fn pay(ctx: Context<Pay>, amount: u64) -> Result<()> {
        ctx.accounts.treasury.sub_lamports(amount)?;
        ctx.accounts.recipient.add_lamports(amount)?;
        let treasury = &mut ctx.accounts.treasury;
        treasury.total_paid = treasury.total_paid.checked_add(amount).ok_or(TreasuryError::Overflow)?;
        emit!(Paid { recipient: ctx.accounts.recipient.key(), amount });
        Ok(())
    }

    pub fn set_authority(ctx: Context<SetAuthority>, new_authority: Pubkey) -> Result<()> {
        ctx.accounts.treasury.authority = new_authority;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = authority, space = 8 + Treasury::INIT_SPACE)]
    pub treasury: Account<'info, Treasury>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Pay<'info> {
    #[account(mut, has_one = authority)]
    pub treasury: Account<'info, Treasury>,
    /// CHECK: compared with treasury.authority by has_one
    pub authority: UncheckedAccount<'info>,
    /// CHECK: any account may receive a payment
    #[account(mut)]
    pub recipient: UncheckedAccount<'info>,
}

#[derive(Accounts)]
pub struct SetAuthority<'info> {
    #[account(mut, has_one = authority)]
    pub treasury: Account<'info, Treasury>,
    pub authority: Signer<'info>,
}

#[account]
#[derive(InitSpace)]
pub struct Treasury {
    pub authority: Pubkey,
    pub total_paid: u64,
}

#[event]
pub struct Paid {
    pub recipient: Pubkey,
    pub amount: u64,
}

#[error_code]
pub enum TreasuryError {
    #[msg("total_paid overflowed")]
    Overflow,
}
