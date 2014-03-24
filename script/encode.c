#include <stdio.h>
#include <string.h>
#include <stdlib.h>

char * urlencode(char const *s, int len, int *new_length)
{
    char const *from, *end;
    char *start,*to;
    from = s;
    end = s + len;
    start = to = (char *) malloc(3 * len + 1);
    char c;

    char hexchars[] = "0123456789ABCDEF";

    while (from < end) {
        c = *from++;

        if (c == ' ') {
            *to++ = '+';
        } else if ((c < '0' && c != '-' && c != '.')
                   ||(c < 'A' && c > '9')
                   ||(c > 'Z' && c < 'a' && c != '_')
                   ||(c > 'z')) {
            to[0] = '%';
            to[1] = hexchars[c >> 4];
            to[2] = hexchars[c & 15];
            to += 3;
        } else {
            *to++ = c;
        }
    }
    *to = 0;
    if (new_length) {
        *new_length = to - start;
    }
    return (char *) start;

}

int main(int argc,char *argv[])
{

	if(argc!=2){
		exit(1);
	}

	char *s_url=argv[1];
	int url_len=0;

	printf("%s\n",urlencode(s_url,strlen(s_url),&url_len));
	return 0;
}
