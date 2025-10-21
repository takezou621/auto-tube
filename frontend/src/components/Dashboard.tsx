import { useQuery } from '@apollo/client';
import gql from 'graphql-tag';

interface DashboardProps {
  token: string | null;
}

const GET_USER = gql`
  query GetUser {
    user {
      id
      username
      email
    }
  }
`;

export default function Dashboard({ token }: DashboardProps) {
  const { loading, error, data } = useQuery(GET_USER, {
    context: {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  });

  if (loading) return <div className="text-center">読み込み中...</div>;
  if (error) return <div className="text-center text-red-600">エラーが発生しました</div>;

  const user = data?.user;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">ユーザー情報</h2>
        {user && (
          <div className="space-y-2">
            <p><strong>ユーザー名:</strong> {user.username}</p>
            <p><strong>メールアドレス:</strong> {user.email}</p>
          </div>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">QMS機能</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
            <h3 className="font-medium">品質チェック記録</h3>
            <p className="text-sm text-gray-600">品質チェックの記録・管理</p>
          </div>
          <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
            <h3 className="font-medium">検査結果管理</h3>
            <p className="text-sm text-gray-600">検査結果の記録・管理</p>
          </div>
          <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
            <h3 className="font-medium">是正処置管理</h3>
            <p className="text-sm text-gray-600">是正処置の記録・管理</p>
          </div>
          <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
            <h3 className="font-medium">レポート出力</h3>
            <p className="text-sm text-gray-600">品質レポートの生成・出力</p>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">システムステータス</h2>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span>データベース接続:</span>
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">正常</span>
          </div>
          <div className="flex items-center justify-between">
            <span>メッセージキュー:</span>
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">正常</span>
          </div>
          <div className="flex items-center justify-between">
            <span>認証システム:</span>
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">正常</span>
          </div>
        </div>
      </div>
    </div>
  );
}
