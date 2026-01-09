/**
 * AI議事録生成＆タスク抽出ツール - Vue.js アプリケーション
 */

const { createApp } = Vue;

// APIのベースURL（環境に応じて変更）
const API_BASE_URL = 'http://localhost:8000';

createApp({
    data() {
        return {
            // フォーム入力データ
            minuteForm: {
                title: '',
                content: '',
                meeting_date: this.getDefaultDateTime()
            },
            
            // 分析結果
            result: {
                summary: '',
                tasks: []
            },
            
            // 議事録一覧
            minutes: [],
            
            // 選択中の議事録
            selectedMinuteId: null,
            selectedMinute: null,
            
            // UI状態
            isLoading: false,
            isLoadingMinutes: false,
            error: '',
            successMessage: ''
        };
    },
    
    computed: {
        // フォームバリデーション
        isFormValid() {
            return (
                this.minuteForm.title.trim() !== '' &&
                this.minuteForm.content.trim() !== '' &&
                this.minuteForm.meeting_date !== ''
            );
        }
    },
    
    methods: {
        /**
         * デフォルトの日時を取得（現在時刻）
         */
        getDefaultDateTime() {
            const now = new Date();
            // ローカル時間でフォーマット
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            return `${year}-${month}-${day}T${hours}:${minutes}`;
        },
        
        /**
         * 日付をフォーマット
         */
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleString('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        /**
         * MarkdownをHTMLに変換
         */
        renderMarkdown(text) {
            if (!text) return '';
            try {
                return marked.parse(text);
            } catch (e) {
                console.error('Markdown parse error:', e);
                return text;
            }
        },
        
        /**
         * 議事録の分析を実行（作成 → AI分析）
         */
        async analyzeMinute() {
            if (!this.isFormValid) {
                this.error = '全ての項目を入力してください';
                return;
            }
            
            this.isLoading = true;
            this.error = '';
            this.successMessage = '';
            
            try {
                // 1. 議事録を作成
                const createResponse = await fetch(`${API_BASE_URL}/api/v1/minutes`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: this.minuteForm.title,
                        content: this.minuteForm.content,
                        meeting_date: this.minuteForm.meeting_date + ':00'  // 秒を追加
                    })
                });
                
                if (!createResponse.ok) {
                    const errorData = await createResponse.json();
                    throw new Error(errorData.detail || '議事録の作成に失敗しました');
                }
                
                const minute = await createResponse.json();
                console.log('Created minute:', minute);
                
                // 2. AI分析を実行
                const analyzeResponse = await fetch(`${API_BASE_URL}/api/v1/minutes/${minute.id}/analyze`, {
                    method: 'POST'
                });
                
                if (!analyzeResponse.ok) {
                    const errorData = await analyzeResponse.json();
                    throw new Error(errorData.detail || 'AI分析に失敗しました');
                }
                
                const analysisResult = await analyzeResponse.json();
                console.log('Analysis result:', analysisResult);
                
                // 3. 結果を表示
                this.result = {
                    summary: analysisResult.summary,
                    tasks: analysisResult.tasks
                };
                
                // 4. 議事録一覧を更新
                await this.fetchMinutes();
                
                // 5. 作成した議事録を選択状態に
                this.selectedMinuteId = minute.id;
                this.selectedMinute = {
                    ...minute,
                    summary: analysisResult.summary
                };
                
                // 6. フォームをクリア
                this.minuteForm = {
                    title: '',
                    content: '',
                    meeting_date: this.getDefaultDateTime()
                };
                
                this.successMessage = '議事録の分析が完了しました！';
                
            } catch (error) {
                console.error('Error:', error);
                this.error = error.message || '処理中にエラーが発生しました';
            } finally {
                this.isLoading = false;
            }
        },
        
        /**
         * 議事録一覧を取得
         */
        async fetchMinutes() {
            this.isLoadingMinutes = true;
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/minutes`);
                
                if (!response.ok) {
                    throw new Error('議事録一覧の取得に失敗しました');
                }
                
                const data = await response.json();
                // 新しい順にソート
                this.minutes = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                
            } catch (error) {
                console.error('Error fetching minutes:', error);
                this.error = error.message;
            } finally {
                this.isLoadingMinutes = false;
            }
        },
        
        /**
         * 議事録を選択して詳細を表示
         */
        async selectMinute(minute) {
            this.selectedMinuteId = minute.id;
            this.error = '';
            
            try {
                // 詳細を取得（タスク情報を含む）
                const response = await fetch(`${API_BASE_URL}/api/v1/minutes/${minute.id}`);
                
                if (!response.ok) {
                    throw new Error('議事録の取得に失敗しました');
                }
                
                const data = await response.json();
                this.selectedMinute = data;
                
                // 結果を表示
                this.result = {
                    summary: data.summary || '',
                    tasks: data.tasks || []
                };
                
            } catch (error) {
                console.error('Error fetching minute:', error);
                this.error = error.message;
            }
        },
        
        /**
         * 議事録を削除
         */
        async deleteMinute(minuteId) {
            if (!confirm('この議事録を削除してもよろしいですか？\n関連するタスクも削除されます。')) {
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/minutes/${minuteId}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok && response.status !== 204) {
                    throw new Error('削除に失敗しました');
                }
                
                // 一覧から削除
                this.minutes = this.minutes.filter(m => m.id !== minuteId);
                
                // 選択中の議事録が削除された場合はクリア
                if (this.selectedMinuteId === minuteId) {
                    this.selectedMinuteId = null;
                    this.selectedMinute = null;
                    this.result = { summary: '', tasks: [] };
                }
                
                this.successMessage = '議事録を削除しました';
                
            } catch (error) {
                console.error('Error deleting minute:', error);
                this.error = error.message;
            }
        },
        
        /**
         * 選択中の議事録を再分析
         */
        async reanalyzeMinute() {
            if (!this.selectedMinuteId) return;
            
            this.isLoading = true;
            this.error = '';
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/minutes/${this.selectedMinuteId}/analyze`, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || '再分析に失敗しました');
                }
                
                const result = await response.json();
                
                this.result = {
                    summary: result.summary,
                    tasks: result.tasks
                };
                
                // 一覧を更新
                await this.fetchMinutes();
                
                this.successMessage = '再分析が完了しました！';
                
            } catch (error) {
                console.error('Error:', error);
                this.error = error.message;
            } finally {
                this.isLoading = false;
            }
        }
    },
    
    // アプリケーション起動時に議事録一覧を取得
    mounted() {
        this.fetchMinutes();
    }
}).mount('#app');
