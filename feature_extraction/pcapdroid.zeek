@load base/protocols/conn

module PcapDroid;

export {
    redef record connection += {
        app_name: string &optional;
        app_uid: int &optional;  # Renamed to avoid conflict with Zeek's uid
    };
}

# Function to convert 4 bytes to an unsigned 32-bit integer (big-endian)
function bytes_to_uint32(s: string): count {
    if (|s| != 4) return 0;
    return bytestring_to_count(s);
}

# Function to convert 4 bytes to a signed 32-bit integer
function bytes_to_int32(s: string): int {
    local val: count = bytes_to_uint32(s);
    if (val > 0x7FFFFFFF)
        return (val - 0x100000000) as int;
    else
        return val as int;
}

event raw_packet(p: pkt_hdr) {
    local pkt_len = |p$payload|;
    local min_len = 46;  # Minimum length with trailer
    if (pkt_len < min_len) return;

    # PCAPdroid trailer size (32 bytes)
    local trailer_size = 32;

    # Calculate the trailer's start position
    local trailer_start = pkt_len - trailer_size;

    # Extract the trailer from the payload
    local trailer = sub_bytes(p$payload, trailer_start, trailer_size);

    # Extract fields from the trailer
    local magic_bytes = sub_bytes(trailer, 0, 4);
    local magic = bytes_to_uint32(magic_bytes);
    if (magic != 0x01072021) return;  # Magic number doesn't match

    # Extract UID
    local uid_bytes = sub_bytes(trailer, 4, 4);
    local app_uid = bytes_to_int32(uid_bytes);

    # Extract App Name (20 bytes)
    local appname_bytes = sub_bytes(trailer, 8, 20);
    local app_name = appname_bytes;
    app_name = sub(app_name, /\x00+$/, "");  # Remove null terminators

    # Associate with the current connection
    if ( p?$conn && p$conn != null ) {
        p$conn$app_name = app_name;
        p$conn$app_uid = app_uid;
    }
}

# Extend the connection record to include app_name and app_uid in logs
redef record Conn::Info += {
    app_name: string &optional;
    app_uid: int &optional;
};

# Include the new fields in conn.log
redef Conn::default_write_columns += { "app_name", "app_uid" };

event connection_state_remove(c: connection) {
    if ( c?$app_name && c$app_name != "" ) {
        c$info$app_name = c$app_name;
        c$info$app_uid = c$app_uid;
    }
}
