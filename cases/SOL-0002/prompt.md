# Fee vault

A Pinocchio program that holds protocol fees in a program-owned vault account.
A config account records which authority may move fees out of the vault, and
the authority can hand control to a new address.

The program is shown below. Each instruction is selected by the first byte of
the instruction data; the doc comment in `src/lib.rs` lists the accounts each one takes.

## Answer format

(replaced by the harness)
