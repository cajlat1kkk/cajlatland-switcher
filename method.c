// Receives only text-input transactions. No keyboard grab or virtual keyboard.
#include <gio/gio.h>
#include <wayland-client.h>
#include <stdio.h>
#include <signal.h>
#include <sys/signalfd.h>
#include <poll.h>
#include <unistd.h>
#include <glib/gstdio.h>
#include <string.h>
#include "method.h"

typedef struct {
    struct wl_seat *seat;
    struct zwp_input_method_manager_v2 *manager;
    unsigned serial, cursor, last_cursor, fingerprint;
    gboolean active, allowed, fresh, snapshot, stopped;
    char tail[196], manual[4001];
    gboolean selected, paused, removed_word, tracked;
    unsigned rejected_hash, start;
    char *manual_tool, *learn_tool, *pause_file;
    const char *engine, *helper, *config;
} State;

static void reset(State *s) {
    memset(s->tail, 0, sizeof s->tail);
    memset(s->manual,0,sizeof s->manual); s->tracked=FALSE; s->selected=FALSE;
    s->fingerprint = 0; s->snapshot = FALSE;
}
static char *run(const char *const args[], const char *input);
static void activate(void *data, struct zwp_input_method_v2 *im) {
    State *s=data; reset(s);
    const char *args[]={"/usr/bin/python3",s->helper,"check",NULL};
    char *permission=run(args,"");s->active=permission && *permission;g_free(permission);
    s->allowed=FALSE; s->fresh=TRUE;
}
static void deactivate(void *data, struct zwp_input_method_v2 *im) {
    State *s=data; reset(s); s->active=s->allowed=FALSE;
}
static void surrounding(void *data, struct zwp_input_method_v2 *im,
                        const char *text, uint32_t cursor, uint32_t anchor) {
    State *s=data; memset(s->tail,0,sizeof s->tail); s->snapshot=FALSE;
    memset(s->manual,0,sizeof s->manual);
    if (!s->active || cursor>strlen(text) || anchor>strlen(text)) {reset(s);return;}
    s->selected=cursor!=anchor;
    if(s->selected){
        unsigned length=MAX(cursor,anchor)-MIN(cursor,anchor);
        if(length < sizeof s->manual) memcpy(s->manual,text+MIN(cursor,anchor),length);
        s->fingerprint=0; return;
    }
    if(s->tracked && cursor<=s->start){
        if(cursor==s->start)s->removed_word=TRUE;
        else s->tracked=FALSE;
    }
    // Keep at most one candidate token and a boundary until done, even if
    // the toolkit sends an entire paragraph. Suppress truncated tokens.
    size_t end=cursor;
    if(end && g_ascii_isspace(text[end-1])) end--;
    size_t start=end;
    while(start && !g_ascii_isspace(text[start-1])) start--;
    if(cursor-start>=sizeof s->tail) {s->fingerprint=0;return;}
    memcpy(s->tail,text+start,cursor-start); memcpy(s->manual,s->tail,cursor-start); s->cursor=cursor; s->snapshot=TRUE;
}
static void content(void *data, struct zwp_input_method_v2 *im,uint32_t hints,uint32_t purpose) {
    State *s=data;
    s->allowed=(purpose==0 || purpose==1) && !(hints & (64u|128u));
    if(!s->allowed) reset(s);
}
static void cause(void *d,struct zwp_input_method_v2 *im,uint32_t reason) {}
static char *run(const char *const args[], const char *input) {
    GSubprocess *p=g_subprocess_newv(args,G_SUBPROCESS_FLAGS_STDIN_PIPE|G_SUBPROCESS_FLAGS_STDOUT_PIPE|G_SUBPROCESS_FLAGS_STDERR_SILENCE,NULL);
    char *out=NULL;
    if(p && (!g_subprocess_communicate_utf8(p,input,NULL,&out,NULL,NULL)||!g_subprocess_get_successful(p))) g_clear_pointer(&out,g_free);
    g_clear_object(&p); return out;
}
static void done(void *data, struct zwp_input_method_v2 *im) {
    State *s=data; s->serial++;
    if(!s->active || !s->allowed){reset(s);s->fresh=FALSE;return;}
    if(!s->snapshot){s->fresh=FALSE;return;}
    size_t n=strlen(s->tail);
    char delim=n?s->tail[n-1]:0;
    gboolean boundary=delim && strchr(" \t\n!?;:,.",delim);
    if(boundary) s->tail[n-1]=0;
    unsigned hash=g_str_hash(s->tail);
    gboolean typed=boundary && !s->fresh && s->cursor==s->last_cursor+1 && hash==s->fingerprint;
    s->fresh=FALSE; s->snapshot=FALSE; s->last_cursor=s->cursor;
    s->fingerprint=boundary?0:hash;
    if(typed && g_utf8_strlen(s->tail,-1)>=3) {
        GKeyFile *k=g_key_file_new();
        gboolean loaded=g_key_file_load_from_file(k,s->config,G_KEY_FILE_NONE,NULL);
        gboolean enabled=loaded && g_key_file_get_boolean(k,"Switcher","enabled",NULL);
        gboolean layout=g_key_file_get_boolean(k,"Switcher","layout",NULL), typos=g_key_file_get_boolean(k,"Switcher","typos",NULL);
        g_key_file_unref(k);
        if(s->paused)layout=FALSE;
        if(enabled && (layout||typos)){
            const char *args[]={s->engine,"correct",NULL,NULL}; if(!layout)args[2]="--no-layout";else if(!typos)args[2]="--no-typos";
            char *out=run(args,s->tail);
            if(out && *out && strcmp(out,s->tail)){
                const char *check[]={"/usr/bin/python3",s->helper,"check",NULL};
                char *app=run(check,"");
                if(app && *app){
                    gboolean rejected=s->tracked && s->removed_word && hash==s->rejected_hash && s->cursor-n==s->start;
                    const char *learn[]={"/usr/bin/python3",s->learn_tool,rejected?"reject":"check",NULL};
                    char *decision=run(learn,s->tail);
                    gboolean skip=rejected || !decision || strcmp(decision,"ok");
                    g_free(decision);
                    if(skip){g_free(app);g_free(out);memset(s->tail,0,sizeof s->tail);return;}
                    s->start=s->cursor-n;s->rejected_hash=hash;s->tracked=TRUE;s->removed_word=FALSE;
                    s->manual[0]=0;
                    char *insert=g_strdup_printf("%s%c",out,delim);
                    zwp_input_method_v2_delete_surrounding_text(im,n,0);
                    zwp_input_method_v2_commit_string(im,insert);
                    zwp_input_method_v2_commit(im,s->serial);
                    g_free(insert);
                    if(layout && g_unichar_get_script(g_utf8_get_char(out)) != g_unichar_get_script(g_utf8_get_char(s->tail))){
                        const char *group=g_unichar_get_script(g_utf8_get_char(out))==G_UNICODE_SCRIPT_CYRILLIC?"ru":"us";
                        const char *sw[]={"/usr/bin/python3",s->helper,group,app,NULL};
                        g_free(run(sw,""));
                    }
                }
                g_free(app);
            }
            g_free(out);
        }
    }
    memset(s->tail,0,sizeof s->tail);
}
static gboolean option(State *s,const char *name) {
    GKeyFile *k=g_key_file_new();
    gboolean ok=g_key_file_load_from_file(k,s->config,G_KEY_FILE_NONE,NULL);
    gboolean value=ok && (!g_key_file_has_key(k,"Switcher",name,NULL) ||
        g_key_file_get_boolean(k,"Switcher",name,NULL));
    g_key_file_unref(k);return value;
}
static void gesture(State *s,struct zwp_input_method_v2 *im,int sig) {
    if(sig==SIGWINCH){
        if(option(s,"single")){
            const char *cmd[]={"/usr/bin/python3",s->helper,"next",NULL};g_free(run(cmd,""));
        }
        return;
    }
    if(sig==SIGUSR2){
        const char *args[]={"/usr/bin/python3",s->helper,"permitted",NULL};
        char *permission=run(args,"");
        gboolean ok=permission && *permission;g_free(permission);
        if(!ok)return;
        if(option(s,"chord")){
            s->paused=!s->paused;
            if(s->paused)g_file_set_contents(s->pause_file,"1",1,NULL);
            else g_unlink(s->pause_file);
        }
        return;
    }
    if(!option(s,"double") || !s->active || !s->allowed || !*s->manual)return;
    const char *check[]={"/usr/bin/python3",s->helper,"check",NULL};
    char *app=run(check,"");
    if(!app || !*app){g_free(app);return;}
    const char *cmd[]={"/usr/bin/python3",s->manual_tool,NULL};
    char *out=run(cmd,s->manual);
    if(out && *out && strlen(out)<=4000 && strcmp(out,s->manual)){
        if(!s->selected)zwp_input_method_v2_delete_surrounding_text(im,strlen(s->manual),0);
        zwp_input_method_v2_commit_string(im,out);
        zwp_input_method_v2_commit(im,s->serial);
        const char *group=NULL;
        for(const char *p=out;*p;p=g_utf8_next_char(p)){
            GUnicodeScript script=g_unichar_get_script(g_utf8_get_char(p));
            if(script==G_UNICODE_SCRIPT_CYRILLIC){group="ru";break;}
            if(script==G_UNICODE_SCRIPT_LATIN){group="us";break;}
        }
        if(group){const char *sw[]={"/usr/bin/python3",s->helper,group,app,NULL};g_free(run(sw,""));}
        memset(s->manual,0,sizeof s->manual);
    }
    g_free(out);g_free(app);
}
static void unavailable(void *d,struct zwp_input_method_v2 *im){((State*)d)->stopped=TRUE;}
static const struct zwp_input_method_v2_listener listener={activate,deactivate,surrounding,cause,content,done,unavailable};
static void global(void *d,struct wl_registry *r,uint32_t n,const char *iface,uint32_t v){
    State *s=d;
    if(!s->seat && !strcmp(iface,"wl_seat"))s->seat=wl_registry_bind(r,n,&wl_seat_interface,1);
    if(!strcmp(iface,"zwp_input_method_manager_v2"))s->manager=wl_registry_bind(r,n,&zwp_input_method_manager_v2_interface,1);
}
static void removed(void *d,struct wl_registry *r,uint32_t n){}
int main(int argc,char **argv){
    if(argc!=4)return 2;
    State s={.engine=argv[1],.helper=argv[2],.config=argv[3]};
    struct wl_display *display=wl_display_connect(NULL);if(!display)return 1;
    struct wl_registry *registry=wl_display_get_registry(display);
    static const struct wl_registry_listener globals={global,removed};
    wl_registry_add_listener(registry,&globals,&s);
    if(wl_display_roundtrip(display)<0 || !s.manager || !s.seat)return 1;
    struct zwp_input_method_v2 *im=zwp_input_method_manager_v2_get_input_method(s.manager,s.seat);
    zwp_input_method_v2_add_listener(im,&listener,&s);
    char *dir=g_path_get_dirname(s.helper);
    s.manual_tool=g_build_filename(dir,"manual.py",NULL);
    s.learn_tool=g_build_filename(dir,"learning.py",NULL);
    s.pause_file=g_build_filename(g_get_user_runtime_dir(),"cajlatland-switcher.paused",NULL);
    g_unlink(s.pause_file);
    sigset_t mask; sigemptyset(&mask);
    sigaddset(&mask,SIGUSR1);sigaddset(&mask,SIGUSR2);sigaddset(&mask,SIGWINCH);
    sigprocmask(SIG_BLOCK,&mask,NULL);
    int fd=signalfd(-1,&mask,SFD_CLOEXEC);if(fd<0)return 1;
    struct pollfd fds[]={{wl_display_get_fd(display),POLLIN,0},{fd,POLLIN,0}};
    while(!s.stopped){
        if(wl_display_dispatch_pending(display)<0 || wl_display_flush(display)<0)break;
        if(poll(fds,2,-1)<0)continue;
        if(fds[0].revents && wl_display_dispatch(display)<0)break;
        if(fds[1].revents&POLLIN){
            struct signalfd_siginfo info;
            if(read(fd,&info,sizeof info)==sizeof info)gesture(&s,im,info.ssi_signo);
        }
    }
    g_unlink(s.pause_file);close(fd);
    wl_display_disconnect(display);return 1;
}
