#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int urldecode(char *str, int len)
{
    char *dest = str;
    char *data = str;

    int value;
    int c;

    while (len--) {
        if (*data == '+') {
        *dest = ' ';
        }
        else if (*data == '%' && len >= 2 && isxdigit((int) *(data + 1))
                 && isxdigit((int) *(data + 2)))
        {

            c = ((unsigned char *)(data+1))[0];
            if (isupper(c))
                c = tolower(c);
            value = (c >= '0' && c <= '9' ? c - '0' : c - 'a' + 10) * 16;
            c = ((unsigned char *)(data+1))[1];
            if (isupper(c))
                c = tolower(c);
            value += c >= '0' && c <= '9' ? c - '0' : c - 'a' + 10;

            *dest = (char)value ;
            data += 2;
            len -= 2;
        } else {
            *dest = *data;
        }
        data++;
        dest++;
    }
    *dest ='\0';
    printf("%s\n",str);
    return dest - str;
}

int main(int argc,char *argv[])
{

	if(argc!=2){
		exit(1);
	}

	char *s_url=argv[1];
    if(strlen(s_url) > 1023){
        exit(1);
    }

	urldecode(s_url,strlen(s_url));
	return 0;
}
