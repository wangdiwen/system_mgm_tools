#!/usr/bin/expect

set timeout 10

set passwd "1234abcd!@#$@vmediax"
puts "\nroot -> $passwd\n"

spawn scp -P 22222 ./get_product_rpm.py ./build_iso_repo.sh 10.4.89.200:/root
expect {
    "*password:" {
        send "$passwd\n"
    }
}

puts "\nSync the mgm tools ..."
spawn scp -P 22222 -r restful-server web-frontend 10.4.89.200:/usr/local
expect {
    "*password:" {
        send "$passwd\n"
    }
}

expect eof
