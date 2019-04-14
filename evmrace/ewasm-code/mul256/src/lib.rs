extern crate ewasm_api;
extern crate bigint;
extern crate wee_alloc;

#[global_allocator]
static ALLOC: wee_alloc::WeeAlloc = wee_alloc::WeeAlloc::INIT;

#[cfg(not(test))]
#[no_mangle]
pub extern "C" fn main() {
    // calldata: 0x26bceb59802431afcbce1fc194c9eaa417b2fb67dc75a95db0bc7ec6b1c8af11df6a1da9a1f5aac137876480252e5dcac62c354ec0d42b76b0642b6181ed099849ea1d57
    // 0x26bceb59
    // x = 802431afcbce1fc194c9eaa417b2fb67dc75a95db0bc7ec6b1c8af11df6a1da9
    // y = a1f5aac137876480252e5dcac62c354ec0d42b76b0642b6181ed099849ea1d57

    let mut xdata = [0u8; 32];
    ewasm_api::unsafe_calldata_copy(4, 32, &mut xdata);

    let mut ydata = [0u8; 32];
    ewasm_api::unsafe_calldata_copy(4+32, 32, &mut ydata);

    let mut x = bigint::uint::U256::from(xdata);
    let y = bigint::uint::U256::from(ydata);

    //let mut x = bigint::uint::U256::from_dec_str("57959994038014968760265486758930062508658705982181761005482965782719583886761").unwrap();
    //let y = bigint::uint::U256::from_dec_str("73256424658773127163535804335021831172298746951041507200730152637916206734679").unwrap();

    // based on https://github.com/gcolvin/evm-drag-race/blob/550e4e85f4db9c1485d01498d8033ef91c55cd78/mul256c.cpp

    for _i in 0..10000 {
        //x = x*y; x = x*y; x = x*y; x = x*y; x = x*y; x = x*y; x = x*y; x = x*y;
        //x = x*y; x = x*y; x = x*y; x = x*y; x = x*y; x = x*y; x = x*y; x = x*y;

        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;

        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;

        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;

        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;

        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;

        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;

        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;

        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
        x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0; x = x.overflowing_mul(y).0;
    }

    let mut result = [0u8; 32];
    x.to_big_endian(&mut result);

    ewasm_api::finish_data(&result);
}
